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

import common.utilities as utils
from common.dynamodb_utilities import Dynamodb, STACK_NAME
from common.mediaconvert_utilities import MediaConvertClient
from common.s3_utilities import S3Client


STATUS_TABLE = 'FileTransferStatus'
AUDIT_TABLE = 'FileTransferAudit'
PROJECTS_TABLE = 'ResearchProjects'


class IncomingMonitor:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb()
        self.s3_client = S3Client()
        self.known_files = None
        self.active_projects = None

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

    def get_active_projects_info(self):
        self.active_projects = self.ddb_client.scan(
            table_name=PROJECTS_TABLE,
            filter_attr_name="interview_task_status",
            filter_attr_values=['active'],
            correlation_id=self.correlation_id,
        )
        return self.active_projects

    def add_new_file_to_status_table(self, s3_bucket_name, s3_path, head):
        if self.active_projects is None:
            self.get_active_projects_info()
        if not self.active_projects:
            raise utils.ObjectDoesNotExistError(f"No research projects conducting interviews could be found in Dynamodb {PROJECTS_TABLE} table",
                                                details={'active_projects': self.active_projects})

        self.logger.debug('Path of S3 file', extra={'s3_path': s3_path, 's3_bucket_name': s3_bucket_name})
        s3_filename, interview_dir, file_type = parse_s3_path(s3_path)
        metadata = head['Metadata']
        user_id = self.get_user_id_from_core_api(metadata['email'])
        referrer_url = metadata.get('referrer')
        project_id = None
        project_prefix = None

        if referrer_url:  # on-demand interview
            interview_type = 'INT-O'
            question_number = metadata['question_index']
            for p in self.active_projects:
                if p.get('on_demand_referrer') == referrer_url:
                    project_id = p['id']
                    project_prefix = p['filename_prefix']
                    break
            assert project_prefix, f'Referrer url {referrer_url} not found in Dynamodb table {PROJECTS_TABLE}'
            target_basename = f'{project_prefix}_{interview_type}_{user_id}_{question_number}'
        else:  # live interview
            interview_type = 'INT-L'
            interviewer = metadata['interviewer']
            if len(self.active_projects) == 1:
                project = self.active_projects[0]
            else:
                interviewer_matches = list()
                for p in self.active_projects:
                    if interviewer in p['interviewers'].keys():
                        interviewer_matches.append(p)
                assert len(interviewer_matches) == 1, f'Could not resolve project based on interviewer. Interviewer {interviewer} is taking part in ' \
                                                      f'projects: {", ".join(map(lambda m: m["id"], interviewer_matches))}'
                project = interviewer_matches[0]
            project_id = project['id']
            project_prefix = project['filename_prefix']
            interviewer_initials = project['interviewers'][interviewer]['initials']
            target_basename = f'{project_prefix}_{interview_type}_{interviewer_initials}_{user_id}'

        item = {
            'original_filename': s3_filename,
            'original_path': s3_path,
            'source_bucket': s3_bucket_name,
            'interview_id': interview_dir,
            'project_id': project_id,
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


class ProcessIncoming:

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb()
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
        self.ddb_client = Dynamodb()
        self.s3_client = S3Client()

    def get_sftp_parameters(self, project_id):
        sdhs_secret = utils.get_secret("sdhs-connection")
        project_params = sdhs_secret['project_specific_parameters'].get(project_id)
        if project_params is None:
            raise utils.ObjectDoesNotExistError(f'Could not find SDHS parameters for project', details={'project_id': project_id,
                                                                                                        'correlation_id': self.correlation_id})
        target_folder = project_params['folder']
        sdhs_params = dict()
        for param_name in ['host', 'port', 'hostkey', 'hostkey_type', 'username', 'password']:
            param_value = project_params.get(param_name)
            if param_value:
                sdhs_params[param_name] = param_value
            else:
                sdhs_params[param_name] = sdhs_secret.get(param_name)

        sdhs_params['port'] = int(sdhs_params['port'])
        # add host key to connection options
        host_key_str = sdhs_params['hostkey']
        host_key_bytes = bytes(host_key_str, encoding='utf-8')
        key_type = sdhs_params['hostkey_type']
        if key_type == 'ecdsa-sha2-nistp256':
            host_key = paramiko.ECDSAKey(data=decodebytes(host_key_bytes))
        elif key_type == 'ssh-rsa':
            host_key = paramiko.RSAKey(data=decodebytes(host_key_bytes))
        else:
            raise NotImplementedError(f'hostkey_type {key_type} not supported')
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys.add(sdhs_params['host'], sdhs_params['hostkey_type'], host_key)
        del sdhs_params['hostkey']
        del sdhs_params['hostkey_type']
        return sdhs_params, target_folder, cnopts

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
        project_id = item['project_id']
        target_basename = item['target_basename']
        sdhs_params, target_folder, cnopts = self.get_sftp_parameters(project_id)

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
        self.ddb_client = Dynamodb()
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


def parse_s3_path(s3_path):
    s3_dirs, s3_filename = os.path.split(s3_path)
    interview_dir, file_type = s3_dirs.split('/')[-2:]
    return s3_filename, interview_dir, file_type


@utils.lambda_wrapper
def monitor_incoming_bucket(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    incoming_monitor = IncomingMonitor(logger=logger, correlation_id=correlation_id)
    incoming_monitor.main()


@utils.lambda_wrapper
def process_incoming_files(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    processor = ProcessIncoming(logger=logger, correlation_id=correlation_id)
    processor.main()


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
    transfer_manager.transfer_file(s3_object['key'], s3_bucket_name=bucket_name)


@utils.lambda_wrapper
def clear_processed(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    cleaner = Cleaner(logger, correlation_id)
    cleaner.main()


if __name__ == "__main__":
    monitor_incoming_bucket(dict(), None)
