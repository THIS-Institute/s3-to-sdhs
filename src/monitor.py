#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
import json
import os
import traceback

from http import HTTPStatus
from pprint import pprint
from thiscovery_lib.interviews_api_utilities import InterviewsApiClient
from thiscovery_lib.s3_utilities import S3Client

import thiscovery_lib.utilities as utils
from thiscovery_lib.core_api_utilities import CoreApiClient
from thiscovery_lib.dynamodb_utilities import Dynamodb
from common.constants import STACK_NAME, STATUS_TABLE, AUDIT_TABLE, PROJECTS_TABLE
from common.helpers import parse_s3_path, get_appointment_datetime


class InterviewFile:
    def __init__(self, s3_bucket_name, s3_path, active_projects=None, core_api_client=None,
                 ddb_client=None, s3_client=None, logger=None, correlation_id=None):
        self.s3_bucket_name = s3_bucket_name
        self.s3_path = s3_path
        self.correlation_id = correlation_id

        self.active_projects = active_projects
        if active_projects is None:
            self.active_projects = self.ddb_client.scan(
                table_name=PROJECTS_TABLE,
                filter_attr_name="interview_task_status",
                filter_attr_values=['active']
            )
        self.logger = logger
        if logger is None:
            self.logger = utils.get_logger()
        self.core_api_client = core_api_client
        if core_api_client is None:
            self.core_api_client = CoreApiClient(correlation_id=correlation_id)
        self.ddb_client = ddb_client
        if ddb_client is None:
            self.ddb_client = Dynamodb(stack_name=STACK_NAME, correlation_id=correlation_id)
        self.s3_client = s3_client
        if s3_client is None:
            self.s3_client = S3Client()

        self.head = self.s3_client.head_object(s3_bucket_name, s3_path)
        self.user_projects = None
        self.participant_email = None

    def _get_anon_project_specific_user_id(self, user_id, project_id):
        self.user_projects = self.core_api_client.get_userprojects(user_id=user_id)
        for up in self.user_projects:
            if up['project_id'] == project_id:
                return up['anon_project_specific_user_id']
        raise utils.ObjectDoesNotExistError(f'User project not found', details={
            'user_id': user_id,
            'project_id': project_id,
            'correlation_id': self.correlation_id,
        })

    def _parse_on_demand_interview_metadata(self, metadata, user_id):
        project_acronym = None
        project_prefix = None
        project_id = None
        interview_type = 'INT-O'
        referrer_url = metadata.get('referrer')
        question_number = metadata['question_index']
        for p in self.active_projects:
            if p.get('on_demand_referrer') == referrer_url:
                project_acronym = p['id']
                project_prefix = p['filename_prefix']
                project_id = p['project_id']
                break
        assert project_prefix, f'Referrer url {referrer_url} not found in Dynamodb table {PROJECTS_TABLE}'
        anon_project_specific_user_id = self._get_anon_project_specific_user_id(
            user_id=user_id,
            project_id=project_id,
        )
        target_basename = f'{project_prefix}_{interview_type}_{anon_project_specific_user_id}_{question_number}'
        return project_acronym, project_prefix, project_id, anon_project_specific_user_id, target_basename

    def _parse_live_interview_metadata(self, metadata, user_id, s3_path):

        def get_appointment(appointment_type_ids, participant_email, correlation_id=None):
            if appointment_type_ids:
                interviews_client = InterviewsApiClient(correlation_id=correlation_id)
                response = interviews_client.get_appointments_by_type_ids(appointment_type_ids=appointment_type_ids)
                appointments = json.loads(response['body'])['appointments']
                for a in appointments:
                    if a['participant_email'] == participant_email:
                        return get_appointment_datetime(appointment_dict=a, output_format='%Y-%m-%d-%H%M')

        interview_type = 'INT-L'
        interviewer = metadata['interviewer']
        if len(self.active_projects) == 1:
            project = self.active_projects[0]
        else:
            interviewer_matches = list()
            participant_matches = list()
            if self.user_projects is None:
                self.user_projects = self.core_api_client.get_userprojects(user_id=user_id)
            participant_projects = [x['project_id'] for x in self.user_projects]
            for p in self.active_projects:
                if interviewer in p['interviewers'].keys():
                    interviewer_matches.append(p)
                if p['project_id'] in participant_projects:
                    participant_matches.append(p)
            error_message = f'Could not resolve project of file {s3_path}.'
            if not interviewer_matches:
                raise utils.DetailedValueError(
                    f'{error_message} Interviewer {interviewer} is not taking part in any active project',
                    details={'active projects': self.active_projects},
                )
            elif len(interviewer_matches) == 1:
                project = interviewer_matches[0]
            else:
                if not participant_matches:
                    raise utils.DetailedValueError(
                        f'{error_message} Participant {metadata["email"]} is not taking part in any active project.',
                        details={
                            'active projects': self.active_projects,
                            'interviewer_matches': interviewer_matches
                        },
                    )
                common_matches = [x for x in participant_matches if x in interviewer_matches]
                if not common_matches:
                    raise utils.DetailedValueError(
                        f'{error_message} Participant {metadata["email"]} and interviewer {interviewer} active '
                        f'projects do not overlap',
                        details={
                            'active projects': self.active_projects,
                            'interviewer_matches': interviewer_matches,
                            'participant_matches': participant_matches,
                        },
                    )
                elif len(common_matches) == 1:
                    project = common_matches[0]
                else:
                    raise utils.DetailedValueError(
                        f'{error_message} Participant {metadata["email"]} and interviewer {interviewer} are '
                        f'taking part in more than one active project',
                        details={
                            'active projects': self.active_projects,
                            'interviewer_matches': interviewer_matches,
                            'participant_matches': participant_matches,
                        },
                    )
        project_acronym = project['id']
        project_prefix = project['filename_prefix']
        project_id = project['project_id']
        interviewer_initials = project['interviewers'][interviewer]['initials']
        anon_project_specific_user_id = self._get_anon_project_specific_user_id(
            user_id=user_id,
            project_id=project_id,
        )
        target_basename = f'{project_prefix}_{interview_type}_{interviewer_initials}_{anon_project_specific_user_id}'
        appointment_datetime = get_appointment(
            appointment_type_ids=project.get('type_ids'),
            participant_email=self.participant_email,
            correlation_id=self.correlation_id,
        )
        if appointment_datetime:
            target_basename += f'_{appointment_datetime}'
        return project_acronym, project_prefix, project_id, anon_project_specific_user_id, target_basename

    def add_to_status_table(self):
        if not self.active_projects:
            raise utils.ObjectDoesNotExistError(f"No research projects conducting interviews could be found in Dynamodb {PROJECTS_TABLE} table",
                                                details={'active_projects': self.active_projects})
        self.logger.debug('Path of S3 file', extra={'s3_path': self.s3_path, 's3_bucket_name': self.s3_bucket_name})
        s3_filename, interview_dir, file_type = parse_s3_path(self.s3_path)
        metadata = self.head['Metadata']
        self.participant_email = metadata['email']
        user_id = self.core_api_client.get_user_id_by_email(email=self.participant_email)
        referrer_url = metadata.get('referrer')

        if referrer_url:  # on-demand interview
            (
                project_acronym,
                project_prefix,
                project_id,
                anon_project_specific_user_id,
                target_basename
            ) = self._parse_on_demand_interview_metadata(
                metadata=metadata,
                user_id=user_id
            )
        else:  # live interview
            (
                project_acronym,
                project_prefix,
                project_id,
                anon_project_specific_user_id,
                target_basename
            ) = self._parse_live_interview_metadata(
                metadata=metadata,
                user_id=user_id,
                s3_path=self.s3_path,
            )

        item = {
            'original_filename': s3_filename,
            'original_path': self.s3_path,
            'source_bucket': self.s3_bucket_name,
            'interview_id': interview_dir,
            'project_acronym': project_acronym,
            'target_basename': target_basename,
            'audio_extraction_attempts': 0,
            'sdhs_transfer_attempts': 0,
            'processing_status': 'new',
        }
        self.head['uploaded_to_s3'] = str(self.head.get('LastModified'))
        del self.head['LastModified']
        try:
            self.logger.debug('Adding item to FileTransferStatus table', extra={'item': item})
            result = self.ddb_client.put_item(
                table_name=STATUS_TABLE,
                key=self.s3_path,
                item_type=file_type,
                item_details=self.head,
                item=item,
                correlation_id=self.correlation_id
            )
            assert result['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK, f"put_item operation failed with response: {result}"
            return result
        except utils.DetailedValueError:
            raise utils.DetailedValueError(
                f'Key {self.s3_path} already exists in DynamoDb table',
                details={'key': self.s3_path},
            )


class IncomingMonitor:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.core_api_client = CoreApiClient(correlation_id=correlation_id)
        self.ddb_client = Dynamodb(stack_name=STACK_NAME, correlation_id=correlation_id)
        self.s3_client = S3Client()
        self.active_projects = self.ddb_client.scan(
            table_name=PROJECTS_TABLE,
            filter_attr_name="interview_task_status",
            filter_attr_values=['active']
        )
        self.known_files = [x['id'] for x in self.ddb_client.scan(STATUS_TABLE)]

    def main(self, ignore_extensions=['.mp3', '.flac'], bucket_name=None):
        """
        The main processing routine

        Args:
            ignore_extensions (list): list of file extensions to ignore
            bucket_name (str): specify a different target bucket; used for testing

        Returns:
        """
        files_added_to_status_table = list()
        if bucket_name:
            s3_bucket_name = f'{STACK_NAME}-{utils.get_environment_name()}-{bucket_name}'
        else:
            s3_bucket_name = utils.get_secret("incoming-interviews-bucket", namespace_override='/prod/')['name']
        objs = self.s3_client.list_objects(s3_bucket_name)['Contents']
        for o in objs:
            s3_path = o['Key']
            self.logger.debug(f'Working on file {s3_path}')
            folder = s3_path.split('/')[0]

            # skip anything that is not in a uuid-named folder
            try:
                utils.validate_uuid(folder)
            except utils.DetailedValueError:
                continue

            if s3_path not in self.known_files:
                _, extension = os.path.splitext(s3_path)
                if extension and (extension not in ignore_extensions):
                    interview_file = InterviewFile(
                        s3_bucket_name=s3_bucket_name,
                        s3_path=s3_path,
                        active_projects=self.active_projects,
                        logger=self.logger,
                        correlation_id=self.correlation_id,
                        core_api_client=self.core_api_client,
                        ddb_client=self.ddb_client,
                        s3_client=self.s3_client,
                    )
                    try:
                        interview_file.add_to_status_table()
                        files_added_to_status_table.append(s3_path)
                    except:
                        self.logger.error(
                            f'Failed to add {s3_path} to ddb table {STATUS_TABLE}',
                            extra={
                                'traceback': traceback.format_exc()
                            },
                        )
        return files_added_to_status_table

