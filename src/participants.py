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
from thiscovery_lib.lambda_utilities import Lambda
from common.constants import STACK_NAME, STATUS_TABLE, AUDIT_TABLE, PROJECTS_TABLE
from common.mediaconvert_utilities import MediaConvertClient
from common.helpers import parse_s3_path, get_sftp_parameters
from monitor import IncomingMonitor
from main import TransferManager


class ProjectParser:
    def __init__(self, project_item, core_api_client=None, logger=None, correlation_id=None):
        """

        Args:
            project_item: ddb item from ResearchProjects table
            core_api_client:
            logger:
            correlation_id:
        """
        self.project_acronym = project_item['id']
        self.project_id = project_item['project_id']
        self.logger = logger
        if logger is None:
            self.logger = utils.get_logger()
        self.core_api_client = core_api_client
        if core_api_client is None:
            self.core_api_client = CoreApiClient(correlation_id=correlation_id)

        self.users = None

    def _get_users(self):
        if self.users is None:
            self.users = self.core_api_client.list_users_by_project(project_id=self.project_id)
        return self.users

    def transfer_participant_csv(self):
        sdhs_params, target_folder, cnopts = get_sftp_parameters(self.project_acronym)
        target_filename = f'{self.project_acronym}_participants_{utils.now_with_tz().strftime("%Y-%m-%d")}.csv'
        with pysftp.Connection(**sdhs_params, cnopts=cnopts) as sftp:
            sftp.chdir(target_folder)
            with sftp.sftp_client.open(target_filename, 'w') as csvfile:
                fieldnames = [
                    'anon_project_specific_user_id',
                    'first_name',
                    'last_name',
                    'email',
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.users)
        self.logger.debug(f'Completed transfer', extra={
            'csv_filename': target_filename,
        })


class ParticipantInfoTransfer:
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
        for project in self.projects_to_process:
            response = self.lambda_client.invoke(
                function_name=''
            )


@utils.lambda_wrapper
def parse_project_participants(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']


@utils.lambda_wrapper
def participants_to_sdhs(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
