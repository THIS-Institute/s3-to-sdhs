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
import unittest
from http import HTTPStatus
from pprint import pprint

import thiscovery_lib.utilities as utils
import tests.test_data as td
import tests.testing_utilities as test_utils
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.lambda_utilities import Lambda
from src.common.constants import STATUS_TABLE, STACK_NAME
from src.main import TransferManager


class TestTransferManager(test_utils.SdhsTransferTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().populate_status_table()
        cls.ddb_client = Dynamodb(stack_name=STACK_NAME)
        cls.transfer_manager = TransferManager(utils.get_logger())

    def mark_audio_extraction_submitted(self, key):
        self.ddb_client.update_item(
            table_name=STATUS_TABLE,
            key=key,
            name_value_pairs={
                "processing_status": "audio extraction job submitted",
            },
        )

    def test_get_target_basename(self):
        self.mark_audio_extraction_submitted('f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/'
                                             '61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4')
        target_basename = self.transfer_manager.get_item_and_validate_status('f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/'
                                                                             '61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4')['target_basename']
        self.assertEqual(
            td.test_s3_files['f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4']['expected_target_basename'],
            target_basename
        )

    def test_get_sftp_parameters(self):
        sdhs_params, target_folder, cnopts = self.transfer_manager.get_sftp_parameters('unittest-1')
        self.assertEqual('ftpuser', target_folder)
        self.assertEqual('ftpuser', sdhs_params['username'])
        self.assertCountEqual(['username', 'password', 'host', 'port'], sdhs_params.keys())

    def test_update_status_of_processed_item(self):
        key = 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4'
        r = self.ddb_client.update_item(STATUS_TABLE, key, {
            'processing_status': 'audio extraction job submitted'
        })
        self.assertEqual(HTTPStatus.OK, r['ResponseMetadata']['HTTPStatusCode'])
        item = self.transfer_manager.get_item_and_validate_status(key)
        result = self.transfer_manager.update_status_of_processed_item(item, key)
        self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])

    def test_transfer_file(self):
        file_keys = [
            'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp3',
            'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp3',
        ]
        bucket_name = f'{STACK_NAME}-{utils.get_environment_name()}-interview-audio'
        for k in file_keys:
            self.mark_audio_extraction_submitted(k.replace('.mp3', '.mp4'))
            result = self.transfer_manager.transfer_file(k, bucket_name)
            self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])

    @unittest.skipUnless(os.environ['TEST_ON_AWS'] == 'True', 'Invokes lambda on AWS')
    def test_transfer_file_working_on_aws(self):
        """
        To prevent a real transfer to SDHS, this test invokes TransferFile using a non-existent
        s3 object key, so we should expect an error in the response
        """
        test_s3_event = {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "eu-west-1",
                    "eventTime": "2020-10-13T11:03:26.628Z",
                    "eventName": "ObjectCreated:CompleteMultipartUpload",
                    "userIdentity": {
                        "principalId": "redacted"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "redacted"
                    },
                    "responseElements": {
                        "x-amz-request-id": "redacted",
                        "x-amz-id-2": "redacted"
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "redacted",
                        "bucket": {
                            "name": f"{STACK_NAME}-{utils.get_environment_name()}-interview-audio",
                            "ownerIdentity": {
                                "principalId": "redacted"
                            },
                            "arn": "redacted"
                        },
                        "object": {
                            "key": f"NA_{self.test_keys[0].replace('.mp4', '.mp3')}",
                            "size": 238220928,
                            "eTag": "redacted",
                            "sequencer": "redacted"
                        }
                    }
                }
            ],
            "correlation_id": "0c4e6f9b-8e42-463b-a4b1-661d346944c3",
            "logger": "<Logger thiscovery (DEBUG)>"
        }

        lambda_client = Lambda(stack_name=STACK_NAME)
        response = lambda_client.invoke(
            function_name='TransferFile',
            payload=test_s3_event,
        )
        self.assertIn('FunctionError', response.keys())
        # check ddb get_item returned None for non-existent key
        self.assertEqual('TypeError', response['Payload']['errorType'])
        self.assertEqual("'NoneType' object is not subscriptable", response['Payload']['errorMessage'])
