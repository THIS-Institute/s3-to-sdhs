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
from time import sleep

import tests.testing_utilities as test_utils
from src.main import IncomingMonitor, ProcessIncoming, TransferManager
from src.common.constants import STATUS_TABLE


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
        expected_result = [
            'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
            'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4',
        ]
        files_added_to_status_table = self.monitor.main(bucket_name='mockincomingbucket')
        self.assertCountEqual(expected_result, files_added_to_status_table)

        # create MediaConvert jobs
        self.incoming_processor.main()
        for k in expected_result:
            self.check_item_processing_status(k, 'audio extraction job submitted')

        # check item status is processed (s3 event will trigger transfer, so no need to call transfer process here).
        sleep(15)
        for k in expected_result:
            self.check_item_processing_status(k, 'processed')

        # cleanup
        for k in expected_result:
            self.ddb_client.delete_item(table_name=STATUS_TABLE, key=k)
