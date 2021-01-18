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
import local.dev_config  # sets environment variables for testing
import local.secrets  # sets environment variables for testing
import copy
import os
import unittest

import thiscovery_dev_tools.testing_tools as test_tools
import thiscovery_lib.utilities as utils
import tests.test_data as td
from local.dev_config import TEST_ON_AWS, DELETE_TEST_DATA
from thiscovery_lib.dynamodb_utilities import Dynamodb
from src.main import PROJECTS_TABLE, STATUS_TABLE, STACK_NAME
from src.monitor import IncomingMonitor, InterviewFile


class SdhsTransferTestCase(test_tools.BaseTestCase):
    test_projects = {
        "unittest-1": {
        # "efi": {
            "filename_prefix": "IGNORE-this-test-file",
            "interview_task_status": "active",
            "interviewers": {
                "OliverT": {
                    "initials": "OT",
                    "name": "Oliver Twist"
                },
                "Karolina K": {
                    "initials": "KK",
                    "name": "Karolina Kurts"
                },
                "Brandon": {
                    "initials": "BC",
                    "name": "Brandon Cabrera"
                },
                "THIS Institute": {
                    "initials": "ES",
                    "name": "Emiliano Smartparrot"
                },
                "Joanna E": {
                    "initials": "JE",
                    "name": "Joanna Easton"
                },
            },
            "project_id": "7c18c259-ace6-4f48-9206-93cd15501348",
            "live_interviews": "true",
            "on_demand_interviews": "true",
            "on_demand_referrer": "https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-1",
            "participant_data_to_sdhs": True,
        },
        "unittest-2": {
            "filename_prefix": "IGNORE-this-test-file-PSFU-05",
            "interview_task_status": "active",
            "interviewers": {
                "OliverT": {
                    "initials": "OT",
                    "name": "Oliver Twist"
                },
                "Karolina K": {
                    "initials": "KK",
                    "name": "Karolina Kurts"
                },
            },
            "project_id": "5907275b-6d75-4ec0-ada8-5854b44fb955",
            "live_interviews": "true",
            "on_demand_interviews": "true",
            "on_demand_referrer": "https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-2",
        },
        "unittest-3": {
            "filename_prefix": "IGNORE-this-test-file-PSFU-06",
            "interview_task_status": "active",
            "interviewers": {
                "Joanna E": {
                    "initials": "JE",
                    "name": "Joanna Easton"
                },
            },
            "project_id": "ce36d4d9-d3d3-493f-98e4-04f4b29ccf49",
            "live_interviews": "true",
            "on_demand_interviews": "true",
            "on_demand_referrer": "https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-3",
        },
    }

    test_keys = [
        'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
        'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb_client = Dynamodb(stack_name=STACK_NAME)
        cls.ddb_client.delete_all(STATUS_TABLE)
        for k, v in cls.test_projects.items():
            cls.ddb_client.put_item(
                table_name=PROJECTS_TABLE,
                key=k,
                item_type='test_project',
                item_details=None,
                item=v,
                update_allowed=True,
            )

    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            for k, _ in cls.test_projects.items():
                cls.ddb_client.delete_item(
                    table_name=PROJECTS_TABLE,
                    key=k
                )
            cls.ddb_client.delete_all(STATUS_TABLE)
        super().tearDownClass()

    @classmethod
    def populate_status_table(cls):
        for k in cls.test_keys:
            file = InterviewFile(
                s3_bucket_name=f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket',
                s3_path=k
            )
            file.add_to_status_table()
