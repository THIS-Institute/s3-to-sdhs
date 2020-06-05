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
import os
from http import HTTPStatus
from pprint import pprint

import common.utilities as utils
from common.dynamodb_utilities import Dynamodb
from common.s3_utilities import S3Client


class ProcessManager:
    status_table = 'FileTransferStatus'

    def __init__(self, logger, correlation_id=None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.ddb_client = Dynamodb()
        self.s3_client = S3Client()
        self.known_files = None

    # def scan_bucket(self, bucket_name, filter_in={'ContentType': 'video/mp4'}):
    #     """
    #     Args:
    #         bucket_name:
    #         filter_in: dictionary of attributes names and values to be checked in s3_object header (metadata);
    #                    objects matching any of the set filters will be returned (OR match)
    #                    set this to None if no filter is to be applied
    #
    #     Returns:
    #         Dict of key, metadata pairs for s3 objects of interest
    #     """
    #     metadata_dict = dict()
    #     objs = self.s3_client.list_objects(bucket_name)['Contents']
    #     for o in objs:
    #         o_key = o['Key']
    #         add_to_dict = False
    #         head = self.s3_client.head_object(bucket_name, o_key)
    #
    #         try:
    #             for k, v in filter_in.items():
    #                 if head[k] == v:
    #                     add_to_dict = True
    #         except AttributeError:
    #             # no filter applied
    #             add_to_dict = True
    #
    #         if add_to_dict:
    #             metadata_dict[o_key] = head
    #
    #     return metadata_dict

    def parse_s3_path(self, s3_path):
        s3_dirs, s3_filename = os.path.split(s3_path)
        interview_dir, file_type = s3_dirs.split('/')
        return s3_filename, interview_dir, file_type

    def process_known_file(self, s3_path, head):
        s3_filename, interview_dir, file_type = self.parse_s3_path(s3_path)
        item = self.ddb_client.get_item(self.status_table, s3_path, self.correlation_id)
        pprint(item)

    def process_new_file(self, s3_path, head):
        s3_filename, interview_dir, file_type = self.parse_s3_path(s3_path)
        item = {
            'original_filename': s3_filename,
            'original_path': s3_path,
            'interview_id': interview_dir,
            'processing_status': 'new',
        }
        del head['LastModified']
        try:
            self.logger.debug('Adding item to FileTransferStatus table', extra={'item': item})
            result = self.ddb_client.put_item(
                table_name=self.status_table,
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
        self.known_files = [x['id'] for x in self.ddb_client.scan(self.status_table)]
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

            if process_file:
                if s3_path in self.known_files:
                    self.process_known_files(s3_path, head)
                else:
                    self.process_new_file(s3_path, head)


@utils.lambda_wrapper
def monitor_incoming_bucket(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    process_manager = ProcessManager(logger=logger, correlation_id=correlation_id)
    process_manager.main()


if __name__ == "__main__":
    monitor_incoming_bucket(dict(), None)
