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
from src.monitor import IncomingMonitor, InterviewFile


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
        cls.bucket_name = f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket'

    def get_interview_file(self, s3_path):
        return InterviewFile(
            s3_bucket_name=self.bucket_name,
            s3_path=s3_path,
            active_projects=self.monitor.active_projects,
            core_api_client=self.monitor.core_api_client,
            ddb_client=self.monitor.ddb_client,
            s3_client=self.monitor.s3_client,
            logger=self.monitor.logger,
        )

    def test_01_parse_on_demand_interview_metadata_ok(self):
        k = 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4'
        interview_file = self.get_interview_file(k)
        v = td.test_s3_files[k]
        result = interview_file._parse_on_demand_interview_metadata(
            metadata=v['head']['Metadata'],
            user_id=v['user_id'],
        )
        expected_result = (
            'unittest-1',
            'IGNORE-this-test-file',
            '7c18c259-ace6-4f48-9206-93cd15501348',
            '3b76f205-762d-4fad-a06f-60f93bfbc5a9',
            'IGNORE-this-test-file_INT-O_3b76f205-762d-4fad-a06f-60f93bfbc5a9_10',
        )
        self.assertEqual(expected_result, result)

    def test_02_parse_live_interview_metadata_ok(self):
        k = 'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4'
        interview_file = self.get_interview_file(k)
        v = td.test_s3_files[k]
        result = interview_file._parse_live_interview_metadata(
            metadata=v['head']['Metadata'],
            user_id=v['user_id'],
            s3_path=k,
        )
        expected_result = (
            'unittest-1',
            'IGNORE-this-test-file',
            '7c18c259-ace6-4f48-9206-93cd15501348',
            '3b76f205-762d-4fad-a06f-60f93bfbc5a9',
            'IGNORE-this-test-file_INT-L_KK_3b76f205-762d-4fad-a06f-60f93bfbc5a9',
        )
        self.assertEqual(expected_result, result)

    def test_03_parse_live_interview_interviewer_unknown(self):
        k = '01f4fc68-6843-475d-bbd8-e77064413e09/video/21d1cf26-5c26-4095-9d75-528135c3813c.mp4'
        interview_file = self.get_interview_file(k)
        v = td.test_s3_files[k]
        with self.assertRaises(utils.DetailedValueError) as context:
            interview_file._parse_live_interview_metadata(
                metadata=v['head']['Metadata'],
                user_id=v['user_id'],
                s3_path=k,
            )
        err = context.exception
        pprint(err)
        err_msg = err.args[0]
        self.assertIn('Interviewer Olivia P is not taking part in any active project', err_msg)

    def test_04_parse_live_interview_participant_not_taking_part_in_active_projects(self):
        k = 'dd2150f3-fec9-4ab3-90af-98d28a70d7f2/video/0002fe76-1a84-4039-8a52-795513cdd091.mp4'
        interview_file = self.get_interview_file(k)
        v = td.test_s3_files[k]
        with self.assertRaises(utils.DetailedValueError) as context:
            interview_file._parse_live_interview_metadata(
                metadata=v['head']['Metadata'],
                user_id=v['user_id'],
                s3_path=k,
            )
        err = context.exception
        pprint(err)
        err_msg = err.args[0]
        self.assertIn(
            'Participant fred@email.co.uk is not taking part in any active project.',
            err_msg
        )

    def test_05_parse_live_interview_participant_and_interviewer_projects_do_not_overlap(self):
        k = '427ff1f2-f0cf-4719-a1cf-1a561c1ba496/video/8a1fdf5a-061b-41a6-bee9-36ac3fba3fee.mp4'
        interview_file = self.get_interview_file(k)
        v = td.test_s3_files[k]
        with self.assertRaises(utils.DetailedValueError) as context:
            interview_file._parse_live_interview_metadata(
                metadata=v['head']['Metadata'],
                user_id=v['user_id'],
                s3_path=k,
            )
        err = context.exception
        pprint(err)
        err_msg = err.args[0]
        self.assertIn(
            'Participant eddie@email.co.uk and interviewer Karolina K active projects do not overlap',
            err_msg
        )

    def test_06_parse_live_interview_cannot_resolve_project_error(self):
        k = 'bc2c1b30-1777-49af-b93e-2d7e9e92ac99/video/ba56e21b-3b88-4ce1-a3eb-26d8d4529bd3.mp4'
        interview_file = self.get_interview_file(k)
        v = td.test_s3_files[k]
        with self.assertRaises(utils.DetailedValueError) as context:
            interview_file._parse_live_interview_metadata(
                metadata=v['head']['Metadata'],
                user_id=v['user_id'],
                s3_path=k,
            )
        err = context.exception
        pprint(err)
        err_msg = err.args[0]
        self.assertIn(
            'Participant clive@email.co.uk and interviewer OliverT are taking part in '
            'more than one active project',
            err_msg
        )

    def test_07_add_new_on_demand_video_file_to_status_table_ok(self):
        k = 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4'
        interview_file = self.get_interview_file(k)
        result = interview_file.add_to_status_table()
        self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])
        item = self.ddb_client.get_item(STATUS_TABLE, key=k)
        self.assertEqual(td.test_s3_files[k]['expected_target_basename'], item['target_basename'])
        self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)

    def test_08_add_new_live_interview_file_to_status_table_ok(self):
        k = 'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4'
        interview_file = self.get_interview_file(k)
        result = interview_file.add_to_status_table()
        self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])
        item = self.ddb_client.get_item(STATUS_TABLE, key=k)
        self.assertEqual(td.test_s3_files[k]['expected_target_basename'], item['target_basename'])
        self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)

    def test_09_incoming_monitor_main(self):
        files_added_to_status_table = self.monitor.main(bucket_name='mockincomingbucket')
        self.assertCountEqual(self.test_files_keys, files_added_to_status_table)
        for k in self.test_files_keys:
            item = self.ddb_client.get_item(STATUS_TABLE, key=k)
            self.assertEqual(td.test_s3_files[k]['expected_target_basename'], item['target_basename'])
            self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)

    @unittest.skipUnless(os.environ['TEST_ON_AWS'] == 'True', 'Invokes lambda on AWS')
    def test_10_monitor_lambda_working_on_aws(self):
        lambda_client = Lambda(stack_name=STACK_NAME)
        response = lambda_client.invoke(
            function_name='MonitorIncomingBucket'
        )
        self.assertNotIn('FunctionError', response.keys())
        self.assertCountEqual(self.test_files_keys, response['Payload'])
