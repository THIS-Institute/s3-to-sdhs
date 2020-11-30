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
from thiscovery_lib.dynamodb_utilities import Dynamodb
from common.constants import STACK_NAME, STATUS_TABLE, AUDIT_TABLE, PROJECTS_TABLE
from common.mediaconvert_utilities import MediaConvertClient
from common.helpers import parse_s3_path, get_sftp_parameters
from monitor import IncomingMonitor


class ProcessIncoming:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(stack_name=STACK_NAME)
        self.media_convert_client = MediaConvertClient()

    def main(self):
        new_items = self.ddb_client.scan(STATUS_TABLE, filter_attr_name='processing_status', filter_attr_values=['new'])
        self.logger.info('new_items', extra={'count': str(len(new_items))})
        responses = list()
        for i in new_items:
            key = i['id']
            media_convert_response = self.media_convert_client.create_audio_extraction_job(input_bucket_name=i["source_bucket"], input_file_s3_key=key)
            ddb_response = self.ddb_client.update_item(
                table_name=STATUS_TABLE,
                key=key,
                name_value_pairs={
                    "audio_extraction_attempts": i["audio_extraction_attempts"] + 1,
                    "processing_status": "audio extraction job submitted",
                },
                correlation_id=self.correlation_id
            )
            responses.append((media_convert_response, ddb_response))
        return responses


class TransferManager:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(stack_name=STACK_NAME)
        self.s3_client = S3Client()

    def update_status_of_processed_item(self, item, status_table_key):
        return self.ddb_client.update_item(
            table_name=STATUS_TABLE,
            key=status_table_key,
            name_value_pairs={
                "sdhs_transfer_attempts": item["sdhs_transfer_attempts"] + 1,
                "processing_status": "processed",
            },
            correlation_id=self.correlation_id
        )

    def get_item_and_validate_status(self, status_table_key):
        item = self.ddb_client.get_item(STATUS_TABLE, key=status_table_key)
        item_status = item['processing_status']
        assert item_status == 'audio extraction job submitted', f'Item processing_status is {item_status}. Expected "audio extraction job submitted"'
        return item

    def transfer_file(self, file_s3_key, s3_bucket_name):
        status_table_key = f'{os.path.splitext(file_s3_key)[0]}.mp4'
        item = self.get_item_and_validate_status(status_table_key)
        if item is None:
            raise utils.ObjectDoesNotExistError(f'Item not found in Dynamodb {STATUS_TABLE} table', details={
                'key': status_table_key,
                'correlation_id': self.correlation_id
            })
        project_acronym = item['project_acronym']
        target_basename = item['target_basename']
        sdhs_params, target_folder, cnopts = get_sftp_parameters(project_acronym)

        self.logger.debug(f'Initiating transfer', extra={'s3_bucket_name': s3_bucket_name, 'file_s3_key': file_s3_key})
        with pysftp.Connection(**sdhs_params, cnopts=cnopts) as sftp:
            sftp.chdir(target_folder)
            # s3_dirs, s3_filename = os.path.split(file_s3_key)
            # self.logger.debug('Path of s3_obj', extra={'s3_dirs': s3_dirs, 's3_filename': s3_filename})
            _, extension = os.path.splitext(file_s3_key)
            target_filename = f'{target_basename}{extension}'
            with sftp.sftp_client.open(target_filename, 'wb') as sdhs_f:
                self.s3_client.download_fileobj(s3_bucket_name, file_s3_key, sdhs_f)
        self.logger.debug(f'Completed transfer', extra={'s3_bucket_name': s3_bucket_name, 'file_s3_key': file_s3_key})

        return self.update_status_of_processed_item(item, status_table_key)


class Cleaner:
    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb(stack_name=STACK_NAME)
        self.s3_client = S3Client()
        self.items_to_be_deleted = None

    def get_old_processed_items(self):
        processed_items = self.ddb_client.scan(STATUS_TABLE, filter_attr_name='processing_status', filter_attr_values=['processed'])
        # todo: refactor this to allow for a project-specific deletion schedule (using ddb table storing project parameters)
        seven_days_ago = utils.now_with_tz() - timedelta(days=7)
        old_proc_items = [x for x in processed_items if parser.isoparse(x['modified']) < seven_days_ago]
        self.items_to_be_deleted = old_proc_items
        return old_proc_items

    @staticmethod
    def resolve_s3_key_of_flac_file(video_file_key):
        s3_filename, interview_dir, file_type = parse_s3_path(k)
        return f'{interview_dir}/audio/{os.path.splitext(s3_filename)[0]}.flac'

    def clean_incoming_bucket(self, s3_bucket_name=None):
        if s3_bucket_name is None:
            s3_bucket_name = utils.get_secret("incoming-interviews-bucket")['name']
        item_keys = list()
        video_keys = [x['id'] for x in self.items_to_be_deleted]
        for k in video_keys:
            item_keys.append(k)
            item_keys.append(self.resolve_s3_key_of_flac_file(k))
        response = self.s3_client.delete_objects(
            bucket=s3_bucket_name,
            keys=item_keys
        )
        return response

    def clean_audio_bucket(self):
        item_keys = [x['id'].replace('.mp4', '.mp3') for x in self.items_to_be_deleted]
        response = self.s3_client.delete_objects(
            bucket=f'{STACK_NAME}-{utils.get_environment_name()}-interview-audio',
            keys=item_keys
        )
        return response

    def move_items_to_audit_table(self):
        audit_table = self.ddb_client.get_table(AUDIT_TABLE)
        copy_responses = list()
        delete_responses = list()
        for i in self.items_to_be_deleted:
            r = audit_table.put_item(Item=i, ConditionExpression='attribute_not_exists(id)')
            assert r['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK, f"put_item operation failed with response: {r}"
            copy_responses.append(r)
            del_r = self.ddb_client.delete_item(STATUS_TABLE, i['id'], correlation_id=self.correlation_id)
            assert del_r['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK, f"delete_item operation failed with response: {del_r}"
            delete_responses.append(del_r)
        return copy_responses, delete_responses

    def main(self):
        self.get_old_processed_items()
        self.clean_incoming_bucket()
        self.clean_audio_bucket()
        self.move_items_to_audit_table()


@utils.lambda_wrapper
def monitor_incoming_bucket(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    incoming_monitor = IncomingMonitor(logger=logger, correlation_id=correlation_id)
    return incoming_monitor.main()


@utils.lambda_wrapper
def process_incoming_files(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    processor = ProcessIncoming(logger=logger, correlation_id=correlation_id)
    return processor.main()


@utils.lambda_wrapper
def transfer_file(event, context):
    """
    Triggered by S3 event when running on AWS
    """
    logger = event['logger']
    correlation_id = event['correlation_id']
    logger.debug('Event', extra={'event': event})
    record = event['Records'][0]['s3']
    bucket_name, s3_object = record['bucket']['name'], record['object']
    transfer_manager = TransferManager(logger, correlation_id)
    logger.debug('Calling transfer_file', extra={'bucket_name': bucket_name, 's3_object': s3_object})
    return transfer_manager.transfer_file(s3_object['key'], s3_bucket_name=bucket_name)


@utils.lambda_wrapper
def clear_processed(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    cleaner = Cleaner(logger, correlation_id)
    return cleaner.main()


if __name__ == "__main__":
    monitor_incoming_bucket(dict(), None)
