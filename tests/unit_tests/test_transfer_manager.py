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
import datetime
import json
import unittest

from dateutil.tz import tzutc
from http import HTTPStatus
from time import sleep

import src.common.utilities as utils
import tests.test_data as td
import tests.testing_utilities as test_utils
from src.common.dynamodb_utilities import Dynamodb, STACK_NAME
from src.main import TransferManager, STATUS_TABLE


class TestTransferManager(test_utils.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb_client = Dynamodb()
        cls.transfer_manager = TransferManager(utils.get_logger())

    def test_get_target_basename(self):
        target_basename = self.transfer_manager.get_item_status('f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/'
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
        r = self.ddb_client.update_item(STATUS_TABLE, key, {'processing_status': 'audio extraction job submitted'})
        self.assertEqual(HTTPStatus.OK, r['ResponseMetadata']['HTTPStatusCode'])
        item = self.transfer_manager.get_item_and_validate_status(key)
        result = self.transfer_manager.update_status_of_processed_item(item, key)
        self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])
