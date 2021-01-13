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
import csv
import pysftp
import thiscovery_lib.utilities as utils

from dateutil import parser
from http import HTTPStatus
from thiscovery_lib.core_api_utilities import CoreApiClient
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.interviews_api_utilities import InterviewsApiClient
from thiscovery_lib.lambda_utilities import Lambda

from common.constants import STACK_NAME, PROJECTS_TABLE
from common.helpers import get_sftp_parameters


class ProjectParser:
    def __init__(self, project_acronym, project_id, filename_prefix, appointment_type_ids=None, core_api_client=None, logger=None, correlation_id=None):
        """
        Args:
            project_acronym (str): CORONET, COPD, etc
            project_id (str): project id in thiscovery db
            filename_prefix (str):
            appointment_type_ids (list): ids of acuity appointment types associated with project
            core_api_client:
            logger:
            correlation_id:
        """
        self.project_acronym = project_acronym
        self.project_id = project_id
        self.filename_prefix = filename_prefix
        self.appointment_type_ids = appointment_type_ids
        self.logger = logger
        self.correlation_id = correlation_id
        if logger is None:
            self.logger = utils.get_logger()
        self.core_api_client = core_api_client
        if core_api_client is None:
            self.core_api_client = CoreApiClient(correlation_id=correlation_id)

        self.users = None
        self.appointments_by_user_id = None
        self.appointments_by_user_email = None

    def _get_appointments(self):
        if self.appointments_by_user_email is None:
            interviews_client = InterviewsApiClient(correlation_id=self.correlation_id)
            appointments = interviews_client.get_appointments_by_type_ids(appointment_type_ids=self.appointment_type_ids)
            self.appointments_by_user_email = {x['participant_email']: x for x in appointments}
            self.appointments_by_user_id = {
                x['anon_project_specific_user_id']: x for x in appointments if x['anon_project_specific_user_id'] is not None
            }
        return self.appointments_by_user_email, self.appointments_by_user_id

    def _get_users(self):
        if self.users is None:
            self.users = self.core_api_client.list_users_by_project(project_id=self.project_id)
        return self.users

    def _parse_user(self, user):
        """
        Args:
            user (dict):

        Returns:
            Dict containing user pid and interview appointment info
        """
        def get_appointment_name(appointment_dict):
            return appointment_dict['appointment_type']['name']

        def get_appontment_datetime(appointment_dict):
            return parser.parse(appointment_dict['acuity_info']['datetime']).strftime('%Y-%m-%d %H:%M')

        user_appointments = set()
        for d, k in [(self.appointments_by_user_email, 'email'), (self.appointments_by_user_id, 'anon_project_specific_user_id')]:
            try:
                user_appointments.add(d[k])
            except KeyError:
                pass

        appointment_type = str()
        appointment_datetime = str()
        if len(user_appointments) == 1:
            a = user_appointments.pop()
            appointment_type = get_appointment_name(a)
            appointment_datetime = get_appontment_datetime(a)
        elif len(user_appointments) > 1:
            appointment_type = '; '.join([get_appointment_name(x) for x in user_appointments])
            appointment_datetime = '; '.join([get_appontment_datetime(x) for x in user_appointments])

        return {
            'appointment_type': appointment_type,
            'appointment_datetime': appointment_datetime,
            **user
        }

    def transfer_participant_csv(self):
        self._get_users()
        self._get_appointments()
        sdhs_params, target_folder, cnopts = get_sftp_parameters(self.project_acronym)
        target_filename = f'{self.filename_prefix}_participants_{utils.now_with_tz().strftime("%Y-%m-%d")}.csv'
        if self.users:
            with pysftp.Connection(**sdhs_params, cnopts=cnopts) as sftp:
                sftp.chdir(target_folder)
                with sftp.sftp_client.open(target_filename, 'w') as csvfile:
                    fieldnames = [
                        'anon_project_specific_user_id',
                        'first_name',
                        'last_name',
                        'email',
                        'appointment_type',
                        'appointment_datetime',
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    for user in self.users:
                        writer.writerow(self._parse_user(user))
            self.logger.debug(f'Completed transfer', extra={
                'csv_filename': target_filename,
            })
        else:
            self.logger.info(f'{self.project_acronym} does not have any participants; skipped', extra={
                'csv_filename': target_filename,
            })
        return HTTPStatus.OK


class ParticipantInfoTransferManager:
    def __init__(self, core_api_client=None, ddb_client=None, logger=None, correlation_id=None):
        self.logger = logger
        if logger is None:
            self.logger = utils.get_logger()
        self.core_api_client = core_api_client
        if core_api_client is None:
            self.core_api_client = CoreApiClient(correlation_id=correlation_id)
        self.ddb_client = ddb_client
        if ddb_client is None:
            self.ddb_client = Dynamodb(stack_name=STACK_NAME, correlation_id=correlation_id)
        self.correlation_id = correlation_id

        self.lambda_client = Lambda(stack_name=STACK_NAME)

        self.projects_to_process = [x for x in self.ddb_client.scan(
            table_name=PROJECTS_TABLE,
            filter_attr_name="participant_data_to_sdhs",
            filter_attr_values=[True]
        ) if x["interview_task_status"] == 'active']

    def process_projects(self):
        results = list()
        for project in self.projects_to_process:
            response = self.lambda_client.invoke(
                function_name='ParseProjectParticipants',
                payload={
                    'project_acronym': project['id'],
                    'project_id': project['project_id'],
                    'filename_prefix': project['filename_prefix'],
                    'appointment_type_ids': project.get('appointment_type_ids'),
                    'correlation_id': self.correlation_id,
                },
                invocation_type='Event'
            )
            results.append(response)
        return results


@utils.lambda_wrapper
def parse_project_participants(event, context):
    """
    Called by participants_to_sdhs for each active project
    """
    project_parser = ProjectParser(
        project_acronym=event['project_acronym'],
        project_id=event['project_id'],
        filename_prefix=event['filename_prefix'],
        appointment_type_ids=event.get('appointment_type_ids'),
        core_api_client=event.get('core_api_client'),
        logger=event.get('logger'),
        correlation_id=event['correlation_id'],
    )
    return project_parser.transfer_participant_csv()


@utils.lambda_wrapper
def participants_to_sdhs(event, context):
    """
    Service entry point
    """
    pitm = ParticipantInfoTransferManager(
        logger=event['logger'],
        correlation_id=event['correlation_id'],
    )
    return pitm.process_projects()
