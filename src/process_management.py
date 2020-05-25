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
import paramiko
import pysftp
from base64 import decodebytes
from http import HTTPStatus

import common.utilities as utils
from common.dynamodb_utilities import Dynamodb
from common.s3_utilities import S3Client


@utils.lambda_wrapper
def monitor_incoming_bucket(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']
    ddb_client = Dynamodb()
    s3_bucket_name = utils.get_secret("incoming-interviews-bucket")['name']
    s3_client = S3Client()
    s3_files = s3_client.list_objects(s3_bucket_name)['Contents']
    for f in s3_files:
        s3_path = f['Key']
        s3_dirs, s3_filename = os.path.split(s3_path)
        interview_dir, file_type = s3_dirs.split('/')
        item = {
            'original_filename': s3_filename,
            'original_path': s3_path,
            'interview_id': interview_dir,
            'processing_status': 'new',
        }
        try:
            logger.debug('Adding item to FileTransferStatus table', extra={'item': item})
            result = ddb_client.put_item(
                table_name='FileTransferStatus',
                key=s3_path,
                item_type=file_type,
                item_details=f,
                item=item,
                correlation_id=correlation_id
            )
            assert result['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK, f"put_item operation failed with response: {result}"
            return result
        except NotImplementedError:
            print('Adding this here as a placeholder for the real error for now')
