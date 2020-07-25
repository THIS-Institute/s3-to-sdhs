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
    # 'unit-test-data/f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
    # 'unit-test-data/f21d28a7-d3a5-42bf-8771-5d205ab67dcb/audio/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.flac',
    # 'unit-test-data/f21d28a7-d3a5-42bf-8771-5d205ab67dcb/audio/b1175609-3d59-4936-ad50-05ecf65ed32e.flac',
    # 'unit-test-data/bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4',
]


def main():
    """
    Based on https://stackoverflow.com/a/55687670

    This function could have been simpler if the copy_from function had been used (it preserves objects' metadata by default),
    but that would have required setting cross-account access between the S3 buckets
    (https://aws.amazon.com/premiumsupport/knowledge-center/cross-account-access-s3/#:~:text=Using%20cross%2Daccount%20IAM%20roles,AWS%20account%20or%20AWS%20services)
    and then assuming the required role (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-api.html).
    Probably worth refactoring it to work in this way when things are calmer (quicker, cheaper and also a good learning exercise).

    Returns:

    """
    source_session = boto3.session.Session(profile_name=utils.namespace2profile('/prod/'))
    source_resource = source_session.resource('s3')
    source_bucket_name = utils.get_secret("incoming-interviews-bucket",
                                          namespace_override='/prod/')['name']

    target_session = boto3.session.Session(profile_name=utils.namespace2profile(utils.get_aws_namespace()))
    target_resource = target_session.resource('s3')
    target_bucket_name = f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket'

    for key in TEST_FILES:
        print(f'Working on {key}')
        source_obj = source_resource.Object(source_bucket_name, key)
        target_obj = target_resource.Object(target_bucket_name, key.replace('unit-test-data/', ''))
        target_obj.put(Body=source_obj.get()['Body'].read(), Metadata=source_obj.metadata)


if __name__ == '__main__':
    main()
