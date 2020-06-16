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
import boto3

import src.common.utilities as utils
from src.common.dynamodb_utilities import STACK_NAME
from src.common.s3_utilities import S3Client

TEST_FILES = [
    'unit-test-data/f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
]


def main():
    """
    Based on https://stackoverflow.com/a/55687670
    Returns:

    """
    # source_session = boto3.session.Session(profile_name=utils.namespace2profile('/prod/'))
    # source_resource = source_session.resource('s3')
    source_bucket_name = utils.get_secret("incoming-interviews-bucket",
                                          namespace_override='/prod/')['name']

    target_session = boto3.session.Session(profile_name=utils.namespace2profile(utils.get_aws_namespace()))
    target_resource = target_session.resource('s3')
    target_bucket_name = f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket'

    for key in TEST_FILES:
        print(f'Working on {key}')
        copy_source = {
            'Bucket': source_bucket_name,
            'Key': key,
        }
        # source_obj = source_resource.Object(source_bucket_name, key)
        target_obj = target_resource.Object(target_bucket_name, key.replace('unit-test-data/', ''))
        target_obj.copy_from(CopySource=copy_source)


if __name__ == '__main__':
    main()
