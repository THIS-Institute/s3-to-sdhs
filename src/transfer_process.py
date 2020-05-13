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
import common.utilities as utils
from common.s3_utilities import S3Client


# def get_object_from_s3(s3_bucket_name, object_key, region=None, correlation_id=None):
#     if region is None:
#         region = utils.DEFAULT_AWS_REGION
#     s3_client = S3Client()
#     obj_http_path = f"http://s3.console.aws.amazon.com/s3/object/{s3_bucket_name}/{object_key}?region={region}"
#     obj = s3_client.get_object(bucket=s3_bucket_name, key=object_key)


@utils.lambda_wrapper
def transfer_files(event, context):
    logger = event['logger']
    logger.debug('Logging event', extra={'event': event})
