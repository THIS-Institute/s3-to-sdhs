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
from src.main import IncomingMonitor, ProcessIncoming, TransferManager, STATUS_TABLE


class TestTransfer(test_utils.SdhsTransferTestCase):
    test_user = {
        'id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
        'email': "delia@email.co.uk",
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.monitor = IncomingMonitor(cls.logger)
        cls.incoming_processor = ProcessIncoming(cls.logger)
        cls.transfer_manager = TransferManager(cls.logger)

    def check_item_processing_status(self, key, expected_status):
        item = self.ddb_client.get_item(table_name=STATUS_TABLE, key=key)
        self.assertEqual(expected_status, item['processing_status'])

    def test_transfer(self):
        for k, v in td.test_s3_files.items():
            # add to status table
            self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)
            head = v['head']
            result = self.monitor.add_new_file_to_status_table(f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket', k, head)
            self.assertEqual(HTTPStatus.OK, result['ResponseMetadata']['HTTPStatusCode'])

            # process added item
            self.incoming_processor.main()
            self.check_item_processing_status(k, 'audio extraction job submitted')

            # check item status is processed
            sleep(15)
            self.check_item_processing_status(k, 'processed')

            # cleanup
            self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)
