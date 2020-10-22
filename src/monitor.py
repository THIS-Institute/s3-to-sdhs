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
import datetime
import json
import os
import paramiko
import pysftp

from base64 import decodebytes
from datetime import timedelta
from dateutil import parser
from http import HTTPStatus
from pprint import pprint
from thiscovery_lib.s3_utilities import S3Client

import thiscovery_lib.utilities as utils
from thiscovery_lib.core_api_utilities import CoreApiClient
from thiscovery_lib.dynamodb_utilities import Dynamodb
from common.constants import STACK_NAME, STATUS_TABLE, AUDIT_TABLE, PROJECTS_TABLE
from common.helpers import parse_s3_path


class IncomingMonitor:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.core_api_client = CoreApiClient(correlation_id=correlation_id)
        self.ddb_client = Dynamodb(stack_name=STACK_NAME, correlation_id=correlation_id)
        self.s3_client = S3Client()
        self.known_files = None
        self.active_projects = None
        self.user_projects = None

    def get_active_projects_info(self):
        self.active_projects = self.ddb_client.scan(
            table_name=PROJECTS_TABLE,
            filter_attr_name="interview_task_status",
            filter_attr_values=['active']
        )
        return self.active_projects

    def get_anon_project_specific_user_id(self, user_id, project_id):
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
        anon_project_specific_user_id = self.get_anon_project_specific_user_id(
            user_id=user_id,
            project_id=project_id,
        )
        target_basename = f'{project_prefix}_{interview_type}_{anon_project_specific_user_id}_{question_number}'
        return project_acronym, project_prefix, project_id, anon_project_specific_user_id, target_basename

    def _parse_live_interview_metadata(self, metadata, user_id, s3_path):
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
                    message=f'{error_message} Interviewer {interviewer} is not taking part in any active project',
                    details={'active projects': self.active_projects},
                )
            elif len(interviewer_matches) == 1:
                project = interviewer_matches[0]
            else:
                if not participant_matches:
                    raise utils.DetailedValueError(
                        message=f'{error_message} Participant {metadata["email"]} is not taking part in any active project.',
                        details={
                            'active projects': self.active_projects,
                            'interviewer_matches': interviewer_matches
                        },
                    )
                common_matches = [x for x in participant_matches if x in interviewer_matches]
                if not common_matches:
                    raise utils.DetailedValueError(
                        message=f'{error_message} Participant {metadata["email"]} and interviewer {interviewer} active '
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
                        message=f'{error_message} Participant {metadata["email"]} and interviewer {interviewer} are '
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
        anon_project_specific_user_id = self.get_anon_project_specific_user_id(
            user_id=user_id,
            project_id=project_id,
        )
        target_basename = f'{project_prefix}_{interview_type}_{interviewer_initials}_{anon_project_specific_user_id}'
        return project_acronym, project_prefix, project_id, anon_project_specific_user_id, target_basename

    def add_new_file_to_status_table(self, s3_bucket_name, s3_path, head):
        if self.active_projects is None:
            self.get_active_projects_info()
        if not self.active_projects:
            raise utils.ObjectDoesNotExistError(f"No research projects conducting interviews could be found in Dynamodb {PROJECTS_TABLE} table",
                                                details={'active_projects': self.active_projects})

        self.logger.debug('Path of S3 file', extra={'s3_path': s3_path, 's3_bucket_name': s3_bucket_name})
        s3_filename, interview_dir, file_type = parse_s3_path(s3_path)
        metadata = head['Metadata']
        user_id = self.core_api_client.get_user_id_by_email(email=metadata['email'])
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
                s3_path=s3_path,
            )

        item = {
            'original_filename': s3_filename,
            'original_path': s3_path,
            'source_bucket': s3_bucket_name,
            'interview_id': interview_dir,
            'project_acronym': project_acronym,
            'target_basename': target_basename,
            'audio_extraction_attempts': 0,
            'sdhs_transfer_attempts': 0,
            'processing_status': 'new',
        }
        head['uploaded_to_s3'] = str(head.get('LastModified'))
        del head['LastModified']
        try:
            self.logger.debug('Adding item to FileTransferStatus table', extra={'item': item})
            result = self.ddb_client.put_item(
                table_name=STATUS_TABLE,
                key=s3_path,
                item_type=file_type,
                item_details=head,
                item=item,
                correlation_id=self.correlation_id
            )
            assert result['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK, f"put_item operation failed with response: {result}"
            return result
        except utils.DetailedValueError:
            self.logger.error(f'Key {s3_path} already exists in DynamoDb table', extra={'key': s3_path})
            raise

    def main(self, ignore_extensions=['.mp3', '.flac'], bucket_name=None):
        """
        The main processing routine

        Args:
            ignore_extensions (list): list of file extensions to ignore
            bucket_name (str): specify a different target bucket; used for testing

        Returns:
        """
        files_added_to_status_table = list()
        self.known_files = [x['id'] for x in self.ddb_client.scan(STATUS_TABLE)]
        if bucket_name:
            s3_bucket_name = f'{STACK_NAME}-{utils.get_environment_name()}-{bucket_name}'
        else:
            s3_bucket_name = utils.get_secret("incoming-interviews-bucket", namespace_override='/prod/')['name']
            # # the approach in the line below does not work on AWS; use a S3 bucket policy to allow access from this lambda instead.
            # self.s3_client = S3Client(utils.namespace2profile('/prod/'))  # use an s3_client with access to production buckets
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
                    head = self.s3_client.head_object(s3_bucket_name, s3_path)
                    self.add_new_file_to_status_table(s3_bucket_name, s3_path, head)
                    files_added_to_status_table.append(s3_path)
        return files_added_to_status_table

