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

import src.common.utilities as utils
import tests.test_data as td
from local.dev_config import TEST_ON_AWS, DELETE_TEST_DATA
from src.common.dynamodb_utilities import Dynamodb, STACK_NAME
from src.main import PROJECTS_TABLE, STATUS_TABLE, IncomingMonitor


def tests_running_on_aws():
    """
    Checks if tests are calling AWS API endpoints
    """
    test_on_aws = os.environ.get('TEST_ON_AWS')
    if test_on_aws is None:
        test_on_aws = TEST_ON_AWS
    elif test_on_aws.lower() == 'false':
        test_on_aws = False
    return test_on_aws


class BaseTestCase(unittest.TestCase):
    """
    Subclass of unittest.TestCase with methods frequently used in Thiscovery testing.
    """
    secrets_client = None

    @classmethod
    def setUpClass(cls):
        utils.set_running_unit_tests(True)
        if cls.secrets_client is None:  # initialise a new secrets_client only if another class instance has not done so yet
            cls.secrets_client = utils.SecretsManager()
        cls.secrets_client.create_or_update_secret('runtime-parameters', {'running-tests': 'true'})
        cls.logger = utils.get_logger()

    @classmethod
    def tearDownClass(cls):
        cls.secrets_client.create_or_update_secret('runtime-parameters', {'running-tests': 'false'})
        utils.set_running_unit_tests(False)


class SdhsTransferTestCase(BaseTestCase):
    test_projects = {
        # "unittest-1": {
        "efi": {
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
            },
            "live_interviews": "true",
            "on_demand_interviews": "true",
            "on_demand_referrer": "https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-1",
        }
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb_client = Dynamodb()
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
        keys = [
            'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
            'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4',
        ]
        cls.monitor = IncomingMonitor(utils.get_logger())
        for k in keys:
            v = td.test_s3_files[k]
            head = copy.deepcopy(v['head'])
            cls.monitor.add_new_file_to_status_table(f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket', k, head)



@unittest.skipIf(not tests_running_on_aws(), "Testing are using local methods and this test only makes sense if calling an AWS API endpoint")
class AlwaysOnAwsTestCase(BaseTestCase):
    """
    Skips tests if tests are running locally
    """
    pass


def _aws_request(method, url, params=None, data=None, aws_api_key=None):
    return utils.aws_request(method, url, AWS_TEST_API, params=params, data=data, aws_api_key=aws_api_key)


# def aws_get(url, params):
#     return _aws_request(method='GET', url=url, params=params)
#
#
# def aws_post(url, request_body):
#     return _aws_request(method='POST', url=url, data=request_body)
#
#
# def aws_patch(url, request_body):
#     return _aws_request(method='PATCH', url=url, data=request_body)
#
#
def _test_request(request_method, local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None, aws_api_key=None,
                  correlation_id=None):
    logger = utils.get_logger()

    if tests_running_on_aws():
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
        logger.info(f'Url passed to _aws_request: {url}', extra={'path_parameters': path_parameters, 'querystring_parameters': querystring_parameters})
        return _aws_request(method=request_method, url=url, params=querystring_parameters, data=request_body, aws_api_key=aws_api_key)
    else:
        event = {}
        if path_parameters is not None:
            event['pathParameters'] = path_parameters
        if querystring_parameters is not None:
            event['queryStringParameters'] = querystring_parameters
        if request_body is not None:
            event['body'] = request_body
        return local_method(event, correlation_id)


# def test_get(local_method, aws_url, path_parameters=None, querystring_parameters=None, aws_api_key=None, correlation_id=None):
#     return _test_request('GET', local_method, aws_url, path_parameters=path_parameters,
#                          querystring_parameters=querystring_parameters, aws_api_key=aws_api_key, correlation_id=correlation_id)
#
#
def test_post(local_method, aws_url, path_parameters=None, request_body=None, correlation_id=None):
    return _test_request('POST', local_method, aws_url, path_parameters=path_parameters, request_body=request_body, correlation_id=correlation_id)


# def test_patch(local_method, aws_url, path_parameters=None, request_body=None, correlation_id=None):
#     return _test_request('PATCH', local_method, aws_url, path_parameters=path_parameters, request_body=request_body, correlation_id=correlation_id)
#
#
# def test_put(local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None, correlation_id=None):
#     return _test_request('PUT', local_method, aws_url, path_parameters=path_parameters,
#                          querystring_parameters=querystring_parameters, request_body=request_body, correlation_id=correlation_id)