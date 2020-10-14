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
import tests.testing_utilities as test_utils  # sets environment variables used in testing
import thiscovery_dev_tools.testing_tools as test_tools
import thiscovery_lib.utilities as utils

from time import sleep

from src.common.mediaconvert_utilities import MediaConvertClient
from src.common.constants import STACK_NAME


class TestMediaConvertClient(test_tools.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_convert_client = MediaConvertClient()

    def test_create_audio_extraction_job(self):
        response = self.media_convert_client.create_audio_extraction_job(
            f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket',
            'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4',
        )
        created_job = response['Job']
        sleep(2)
        response = self.media_convert_client.list_jobs(MaxResults=1)
        listed_job = response['Jobs'][0]
        self.assertEqual(created_job['Id'], listed_job['Id'])
        self.assertIn(listed_job['Status'], ['PROGRESSING', 'COMPLETE'])
