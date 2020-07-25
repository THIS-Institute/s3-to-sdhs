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
from dateutil.tz import tzutc

test_s3_files = {
    'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/video/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.mp4': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 10084809,
            'ContentType': 'video/mp4',
            'ETag': '"c0fe76df38abb72163b583e0da06fbb9"',
            'LastModified': datetime.datetime(2020, 6, 11, 13, 14, 28, tzinfo=tzutc()),
            'Metadata': {
                'email': 'delia@email.co.uk',
                'platform': 'Firefox 75.0 on OS X 10.15',
                'question': 'Are there any harms you can think of that might be associated with the test? They might be physical (e.g. the discomfort of the '
                            'swab), psychological (e.g. anxiety) or other harms (e.g. possible uses that might be made of the information about the test that '
                            'might not be in the interests of individuals).',
                'question_index': '10',
                'referrer': 'https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-1',
                'username': 'Testagain Andagain',
                'videoid': 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '10084809',
                    'content-type': 'video/mp4',
                    'date': 'Thu, 11 Jun 2020 13:23:29 GMT',
                    'etag': '"c0fe76df38abb72163b583e0da06fbb9"',
                    'last-modified': 'Thu, 11 Jun 2020 '
                                  '13:14:28 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': 'WaW/8A7eI8CjisS3/DMNCjVTG9jcknkPBLRxYOTujxhq673l6G51iEN+LypkAB4DwcEwUxN2OUc=',
                    'x-amz-meta-email': 'delia@email.co.uk',
                    'x-amz-meta-platform': 'Firefox 75.0 on '
                                        'OS X 10.15',
                    'x-amz-meta-question': 'Are there any harms you can think of that might be associated with the test? They might be physical (e.g. the '
                                           'discomfort of the swab), psychological (e.g. anxiety) or other harms (e.g. possible uses that might be made of the '
                                           'information about the test that might not be in the interests of individuals).',
                    'x-amz-meta-question_index': '10',
                    'x-amz-meta-referrer': 'https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-1',
                    'x-amz-meta-username': 'Testagain '
                                        'Andagain',
                    'x-amz-meta-videoid': 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb',
                    'x-amz-request-id': 'A6738C5F1915BE19'
                },
                'HTTPStatusCode': 200,
                'HostId': 'WaW/8A7eI8CjisS3/DMNCjVTG9jcknkPBLRxYOTujxhq673l6G51iEN+LypkAB4DwcEwUxN2OUc=',
                'RequestId': 'A6738C5F1915BE19',
                'RetryAttempts': 0
            }
        },
        'expected_target_basename': 'IGNORE-this-test-file_INT-O_35224bd5-f8a8-41f6-8502-f96e12d6ddde_10',
    },
    'f21d28a7-d3a5-42bf-8771-5d205ab67dcb/audio/61ca75b6-2c2e-4d32-a8a6-300bf7fd6fa1.flac': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 1075259,
            'ContentType': 'audio/flac',
            'ETag': '"23439d49e08d4e12150bd25cd92cddfc"',
            'LastModified': datetime.datetime(2020, 6, 11, 13, 14, 28, tzinfo=tzutc()),
            'Metadata': {
                'email': 'delia@email.co.uk',
                'platform': 'Firefox 75.0 on OS X 10.15',
                'question': 'Are there any harms you can think of that might be associated with the test? They might be physical (e.g. the discomfort of the '
                            'swab), psychological (e.g. anxiety) or other harms (e.g. possible uses that might be made of the information about the test that '
                            'might not be in the interests of individuals).',
                'question_index': '10',
                'referrer': 'https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-1',
                'username': 'Testagain Andagain',
                'videoid': 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '1075259',
                    'content-type': 'audio/flac',
                    'date': 'Sat, 25 Jul 2020 14:28:51 GMT',
                    'etag': '"23439d49e08d4e12150bd25cd92cddfc"',
                    'last-modified': 'Thu, 11 Jun 2020 '
                                   '13:14:28 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': 'gsE5hIDe0l6kVrck98V9wyDQO34SpASlWoC1YHhraAgTl2V21bOaaYfcXFOaXGTxlBzcXviZSB8=',
                    'x-amz-meta-email': 'delia@email.co.uk',
                    'x-amz-meta-platform': 'Firefox 75.0 on OS X 10.15',
                    'x-amz-meta-question': 'Are there any harms you can think of that might be associated with the test? They might be physical (e.g. the '
                                           'discomfort of the swab), psychological (e.g. anxiety) or other harms (e.g. possible uses that might be made of the '
                                           'information about the test that might not be in the interests of individuals).',
                    'x-amz-meta-question_index': '10',
                    'x-amz-meta-referrer': 'https://start.myinterview.com/this-institute-university-of-cambridge/unit-test-project-1',
                    'x-amz-meta-username': 'Testagain '
                                         'Andagain',
                    'x-amz-meta-videoid': 'f21d28a7-d3a5-42bf-8771-5d205ab67dcb',
                    'x-amz-request-id': '616562F10E92499D'
                },
            'HTTPStatusCode': 200,
            'HostId': 'gsE5hIDe0l6kVrck98V9wyDQO34SpASlWoC1YHhraAgTl2V21bOaaYfcXFOaXGTxlBzcXviZSB8=',
            'RequestId': '616562F10E92499D',
            'RetryAttempts': 0
            }
        },
    },
    'bf67ce1c-757a-46d6-bed6-13d50e1ff0b5/video/2526a433-58d7-4368-921e-7d85cb042c69.mp4': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 11854359,
            'ContentType': 'application/octet-stream',
            'ETag': '"a2b75be34b503a47d07e3c2d1f73e2fe"',
            'LastModified': datetime.datetime(2020, 7, 23, 11, 32, 52, tzinfo=tzutc()),
            'Metadata': {
                'email': 'delia@email.co.uk',
                'interviewer': 'Karolina K',
                'name': 'Doro test for KK'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '11854359',
                    'content-type': 'application/octet-stream',
                    'date': 'Thu, 23 Jul 2020 11:44:22 GMT',
                    'etag': '"a2b75be34b503a47d07e3c2d1f73e2fe"',
                    'last-modified': 'Thu, 23 Jul 2020 '
                                   '11:32:52 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': '1E23JzggfBKTCU2BTOWDRM+elQW0iP550dezx3ZxGNGnjynvE5G/vSI/GbVCNz6WP+W+4ulQBdo=',
                    'x-amz-meta-email': 'delia@email.co.uk',
                    'x-amz-meta-interviewer': 'Karolina K',
                    'x-amz-meta-name': 'Doro test for KK',
                    'x-amz-request-id': '251EAFC1E7B0D92F'
                },
                'HTTPStatusCode': 200,
                'HostId': '1E23JzggfBKTCU2BTOWDRM+elQW0iP550dezx3ZxGNGnjynvE5G/vSI/GbVCNz6WP+W+4ulQBdo=',
                'RequestId': '251EAFC1E7B0D92F',
                'RetryAttempts': 0
            }
        },
        'expected_target_basename': 'IGNORE-this-test-file_INT-L_KK_35224bd5-f8a8-41f6-8502-f96e12d6ddde',
    },
}
