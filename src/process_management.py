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
from http import HTTPStatus
from pprint import pprint

import common.utilities as utils
from common.dynamodb_utilities import Dynamodb
from common.s3_utilities import S3Client


STATUS_TABLE = 'FileTransferStatus'


class IncomingMonitor:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb()
        self.s3_client = S3Client()
        self.known_files = None

    def parse_s3_path(self, s3_path):
        s3_dirs, s3_filename = os.path.split(s3_path)
        interview_dir, file_type = s3_dirs.split('/')
        return s3_filename, interview_dir, file_type

    @staticmethod
    def get_user_id_from_core_api(email):
        env_name = utils.get_environment_name()
        if env_name == 'prod':
            core_api_url = 'https://api.thiscovery.org/'
        else:
            core_api_url = f'https://{env_name}-api.thiscovery.org/'
        result = utils.aws_get('v1/user', core_api_url, params={'email': email})

        assert result['statusCode'] == HTTPStatus.OK, f'Call to core API returned error: {result}'
        return json.loads(result['body'])['id']

    def add_new_file_to_status_table(self, s3_path, head):
        s3_filename, interview_dir, file_type = self.parse_s3_path(s3_path)
        metadata = head['Metadata']
        question_number = metadata.get('question_index')
        referrer_url = metadata.get('referrer')
        interview_type = 'live'
        project = None
        user_id = self.get_user_id_from_core_api(metadata['email'])
        if referrer_url:
            project = referrer_url.split('/')[-1]
            # todo: consider adding a DynamoDB table mapping project to a short identifier to use in the basename of renamed files

        if question_number:
            interview_type = 'on_demand'
            target_basename = f'{project}_{interview_type}_{user_id}_{question_number}'
        else:
            target_basename = f'{project}_{interview_type}_{user_id}'

        item = {
            'original_filename': s3_filename,
            'original_path': s3_path,
            'interview_id': interview_dir,
            'target_basename': target_basename,
            'audio_extraction_attempts': 0,
            'sdhs_transfer_attempts': 0,
            'processing_status': 'new',
        }
        head['uploaded_to_s3'] = head['LastModified']
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
        except utils.DetailedValueError:
            self.logger.error(f'Key {s3_path} already exists in DynamoDb table', extra={'key': s3_path})

    def main(self, filter_in={'ContentType': 'video/mp4'}):
        """
        The main processing routine

        Args:
            filter_in: dictionary of attributes names and values to be checked in s3_object header (metadata);
                       objects matching any of the set filters will be returned (OR match)
                       set this to None if no filter is to be applied

        Returns:
        """
        self.known_files = [x['id'] for x in self.ddb_client.scan(STATUS_TABLE)]
        s3_bucket_name = utils.get_secret("incoming-interviews-bucket")['name']
        objs = self.s3_client.list_objects(s3_bucket_name)['Contents']
        for o in objs:
            s3_path = o['Key']
            process_file = False
            head = self.s3_client.head_object(s3_bucket_name, s3_path)

            try:
                for k, v in filter_in.items():
                    if head[k] == v:
                        process_file = True
            except AttributeError:
                # no filter applied
                process_file = True

            if process_file and s3_path not in self.known_files:
                self.add_new_file_to_status_table(s3_path, head)


class ProcessingManager:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb()

    def main(self):
        pass
        # notifications = get_notifications(NotificationAttributes.STATUS.value, [NotificationStatus.NEW.value, NotificationStatus.RETRYING.value])
        #
        # logger.info('process_notifications', extra={'count': str(len(notifications))})
        #
        # # note that we need to process all registrations first, then do task signups (otherwise we might try to process a signup for someone not yet registered)
        # signup_notifications = []
        # login_notifications = []
        # for notification in notifications:
        #     notification_type = notification['type']
        #     if notification_type == NotificationType.USER_REGISTRATION.value:
        #         process_user_registration(notification)
        #     elif notification_type == NotificationType.TASK_SIGNUP.value:
        #         # add to list for later processing
        #         signup_notifications.append(notification)
        #     elif notification_type == NotificationType.USER_LOGIN.value:
        #         # add to list for later processing
        #         login_notifications.append(notification)
        #     else:
        #         error_message = f'Processing of {notification_type} notifications not implemented yet'
        #         logger.error(error_message)
        #         raise NotImplementedError(error_message)
        #
        # for signup_notification in signup_notifications:
        #     process_task_signup(signup_notification)
        #
        # for login_notification in login_notifications:
        #     process_user_login(login_notification)


@utils.lambda_wrapper
def monitor_incoming_bucket(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    incoming_monitor = IncomingMonitor(logger=logger, correlation_id=correlation_id)
    incoming_monitor.main()


@utils.lambda_wrapper
def process_interview_files(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    processing_manager = ProcessingManager(logger=logger, correlation_id=correlation_id)
    processing_manager.main()


if __name__ == "__main__":
    monitor_incoming_bucket(dict(), None)
