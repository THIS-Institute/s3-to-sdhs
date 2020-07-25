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
        target_basename = self.transfer_manager.get_target_basename(list(td.test_s3_files.keys())[0])
        self.assertEqual(
            td.test_s3_files['f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4']['target_basename'],
            target_basename
        )
