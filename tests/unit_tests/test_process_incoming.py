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
import copy
import os
import unittest
from http import HTTPStatus
from pprint import pprint

from thiscovery_lib.lambda_utilities import Lambda
import thiscovery_lib.utilities as utils
import tests.test_data as td
import tests.testing_utilities as test_utils
from src.common.constants import STACK_NAME, STATUS_TABLE
from src.main import ProcessIncoming, IncomingMonitor
from src.monitor import InterviewFile


class TestProcessIncoming(test_utils.SdhsTransferTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.process_incoming = ProcessIncoming(utils.get_logger())
        cls.monitor = IncomingMonitor(utils.get_logger())

    def test_main(self):
        keys = [
            'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
            # 'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4',
        ]
        for k in keys:
            file = InterviewFile(
                s3_bucket_name=f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket',
                s3_path=k,
            )
            file.add_to_status_table()
        result = self.process_incoming.main()
        for media_convert_result, ddb_result in result:
            self.assertEqual(
                (HTTPStatus.CREATED, HTTPStatus.OK),
                (media_convert_result['ResponseMetadata']['HTTPStatusCode'], ddb_result['ResponseMetadata']['HTTPStatusCode'])
            )
        self.ddb_client.delete_all(STATUS_TABLE)

    @unittest.skipUnless(os.environ['TEST_ON_AWS'] == 'True', 'Invokes lambda on AWS')
    def test_process_incoming_lambda_working_on_aws(self):
        """
        Invokes function with STATUS_TABLE empty, so returned payload should be an empty list
        """
        lambda_client = Lambda(stack_name=STACK_NAME)
        response = lambda_client.invoke(
            function_name='ProcessIncomingFiles'
        )
        self.assertNotIn('FunctionError', response.keys())
        self.assertEqual(list(), response['Payload'])
