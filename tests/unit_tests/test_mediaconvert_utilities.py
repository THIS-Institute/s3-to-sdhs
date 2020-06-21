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
import tests.testing_utilities as test_utils
from src.common.dynamodb_utilities import Dynamodb, STACK_NAME
# from src.process_management import IncomingMonitor, STATUS_TABLE
from src.common.mediaconvert_utilities import MediaConvertClient


class TestMediaConvertClient(test_utils.BaseTestCase):
    # test_user = {
    #     'id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
    #     'email': "delia@email.co.uk",
    # }

    test_s3_files = {
        'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4': {
            'head': {
                'AcceptRanges': 'bytes',
                'ContentLength': 10084809,
                'ContentType': 'video/mp4',
                'ETag': '"c0fe76df38abb72163b583e0da06fbb9"',
                'LastModified': datetime.datetime(2020, 6, 11, 13, 14, 28, tzinfo=tzutc()),
                'Metadata': {'email': 'delia@email.co.uk',
                             'platform': 'Firefox 75.0 on OS X 10.15',
                             'question': 'Are there any harms you can think of that might be '
                                         'associated with the test? They might be physical '
                                         '(e.g. the discomfort of the swab), psychological '
                                         '(e.g. anxiety) or other harms (e.g. possible uses '
                                         'that might be made of the information about the '
                                         'test that might not be in the interests of '
                                         'individuals).',
                             'question_index': '10',
                             'referrer': 'REDACTED',
                             'username': 'Testagain Andagain',
                             'videoid': 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb'},
                'ResponseMetadata': {'HTTPHeaders': {'accept-ranges': 'bytes',
                                                     'content-length': '10084809',
                                                     'content-type': 'video/mp4',
                                                     'date': 'Thu, 11 Jun 2020 13:23:29 GMT',
                                                     'etag': '"c0fe76df38abb72163b583e0da06fbb9"',
                                                     'last-modified': 'Thu, 11 Jun 2020 '
                                                                      '13:14:28 GMT',
                                                     'server': 'AmazonS3',
                                                     'x-amz-id-2': 'WaW/8A7eI8CjisS3/DMNCjVTG9jcknkPBLRxYOTujxhq673l6G51iEN+LypkAB4DwcEwUxN2OUc=',
                                                     'x-amz-meta-email': 'REDACTED',
                                                     'x-amz-meta-platform': 'Firefox 75.0 on '
                                                                            'OS X 10.15',
                                                     'x-amz-meta-question': 'Are there any '
                                                                            'harms you can '
                                                                            'think of that '
                                                                            'might be '
                                                                            'associated with '
                                                                            'the test? They '
                                                                            'might be '
                                                                            'physical (e.g. '
                                                                            'the discomfort '
                                                                            'of the swab), '
                                                                            'psychological '
                                                                            '(e.g. anxiety) '
                                                                            'or other harms '
                                                                            '(e.g. possible '
                                                                            'uses that might '
                                                                            'be made of the '
                                                                            'information '
                                                                            'about the test '
                                                                            'that might not '
                                                                            'be in the '
                                                                            'interests of '
                                                                            'individuals).',
                                                     'x-amz-meta-question_index': '10',
                                                     'x-amz-meta-referrer': 'REDACTED',
                                                     'x-amz-meta-username': 'Testagain '
                                                                            'Andagain',
                                                     'x-amz-meta-videoid': 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb',
                                                     'x-amz-request-id': 'A6738C5F1915BE19'},
                                     'HTTPStatusCode': 200,
                                     'HostId': 'WaW/8A7eI8CjisS3/DMNCjVTG9jcknkPBLRxYOTujxhq673l6G51iEN+LypkAB4DwcEwUxN2OUc=',
                                     'RequestId': 'A6738C5F1915BE19',
                                     'RetryAttempts': 0}
            }
        }
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # cls.ddb_client = Dynamodb()
        # cls.monitor = IncomingMonitor(utils.get_logger())
        cls.media_convert_client = MediaConvertClient()

    def test_create_audio_extraction_job(self):
        response = self.media_convert_client.create_audio_extraction_job(
            f'{STACK_NAME}-{utils.get_environment_name()}-mockincomingbucket',
            list(self.test_s3_files.keys())[0],
        )
        created_job = response['Job']
        sleep(2)
        response = self.media_convert_client.list_jobs(MaxResults=1)
        listed_job = response['Jobs'][0]
        self.assertEqual(created_job['Id'], listed_job['Id'])
        self.assertIn(listed_job['Status'], ['PROGRESSING', 'COMPLETE'])
