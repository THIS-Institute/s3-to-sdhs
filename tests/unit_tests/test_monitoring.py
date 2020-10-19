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

import thiscovery_lib.utilities as utils
import tests.test_data as td
import tests.testing_utilities as test_utils
from thiscovery_lib.dynamodb_utilities import Dynamodb
from thiscovery_lib.lambda_utilities import Lambda
from src.common.constants import STATUS_TABLE, STACK_NAME
from src.main import IncomingMonitor


class TestMonitoring(test_utils.SdhsTransferTestCase):
    test_user = {
        'id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
        'email': "delia@email.co.uk",
    }
    test_files_keys = [
        'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
        'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb_client = Dynamodb(stack_name=STACK_NAME)
        cls.monitor = IncomingMonitor(utils.get_logger())

    def test_get_user_id_from_core_api(self):
        user_id = self.monitor.get_user_id_from_core_api(self.test_user['email'])
        self.assertEqual(self.test_user['id'], user_id)

    def test_add_new_file_to_status_table(self):
        for k in self.test_files_keys:
            v = td.test_s3_files[k]
            head = copy.deepcopy(v['head'])
            result = self.monitor.add_new_file_to_status_table(f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket', k, head)
            self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])
            self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)

    def test_incoming_monitor_main(self):
        files_added_to_status_table = self.monitor.main(bucket_name='mockincomingbucket')
        self.assertCountEqual(self.test_files_keys, files_added_to_status_table)
        for k in self.test_files_keys:
            item = self.ddb_client.get_item(STATUS_TABLE, key=k)
            self.assertEqual(td.test_s3_files[k]['expected_target_basename'], item['target_basename'])
            self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)

    @unittest.skipUnless(os.environ['TEST_ON_AWS'] == 'True', 'Invokes lambda on AWS')
    def test_monitor_lambda_working_on_aws(self):
        lambda_client = Lambda(stack_name=STACK_NAME)
        response = lambda_client.invoke(
            function_name='MonitorIncomingBucket'
        )
        self.assertNotIn('FunctionError', response.keys())
        self.assertCountEqual(self.test_files_keys, response['Payload'])
