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
    # on-demand video
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
        'expected_target_basename': 'IGNORE-this-test-file_INT-O_3b76f205-762d-4fad-a06f-60f93bfbc5a9_10',
        'user_id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
    },
    # on-demand audio
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
    # live interview; interviewer participating in 2 active projects; participant taking part in only 1 of those
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
        'expected_target_basename': 'IGNORE-this-test-file_INT-L_KK_3b76f205-762d-4fad-a06f-60f93bfbc5a9',
        'user_id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
    },
    # live interview; interviewer unknown
    '01f4fc68-6843-475d-bbd8-e77064413e09/video/21d1cf26-5c26-4095-9d75-528135c3813c.mp4': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 4919976,
            'ContentType': 'binary/octet-stream',
            'ETag': '"582cc904ac7a1d9860230cd6403ed494"',
            'LastModified': datetime.datetime(2020, 10, 22, 9, 50, 10, tzinfo=tzutc()),
            'Metadata': {
                'email': 'delia@email.co.uk',
                'interviewer': 'Olivia P',
                'name': 'OliviaInterviewsDelia'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '4919976',
                    'content-type': 'binary/octet-stream',
                    'date': 'Fri, 23 Oct 2020 09:26:36 GMT',
                    'etag': '"582cc904ac7a1d9860230cd6403ed494"',
                    'last-modified': 'Thu, 22 Oct 2020 '
                                     '09:50:10 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': 'Rd+hO616+t8UhKM5I+q7V3CjVMPkroD3fj2e3Z09A819WNGaXzoZ8EqtbcQVi/hAs0zO3UafsMk=',
                    'x-amz-meta-email': 'delia@email.co.uk',
                    'x-amz-meta-interviewer': 'Olivia P',
                    'x-amz-meta-name': 'OliviaInterviewsDelia',
                    'x-amz-request-id': '9FD3DD781BC92597'
                },
                'HTTPStatusCode': 200,
                'HostId': 'Rd+hO616+t8UhKM5I+q7V3CjVMPkroD3fj2e3Z09A819WNGaXzoZ8EqtbcQVi/hAs0zO3UafsMk=',
                'RequestId': '9FD3DD781BC92597',
                'RetryAttempts': 0
            }
        },
        'expected_target_basename': None,
        'user_id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
    },
    # live interview; interviewer participating in 2 active projects; participant also taking part in those 2 projects
    'bc2c1b30-1777-49af-b93e-2d7e9e92ac99/video/ba56e21b-3b88-4ce1-a3eb-26d8d4529bd3.mp4': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 589603776,
            'ContentType': 'binary/octet-stream',
            'ETag': '"83e77931917ee0d8377cb2fa573047a5-36"',
            'LastModified': datetime.datetime(2020, 10, 22, 11, 37, 57, tzinfo=tzutc()),
            'Metadata': {
                'email': 'clive@email.co.uk',
                'interviewer': 'OliverT',
                'name': 'testclive'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '589603776',
                    'content-type': 'binary/octet-stream',
                    'date': 'Thu, 22 Oct 2020 11:58:33 GMT',
                    'etag': '"83e77931917ee0d8377cb2fa573047a5-36"',
                    'last-modified': 'Thu, 22 Oct 2020 '
                                     '11:37:57 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': 'gF6gD3FeCTsssacCeCBtilYeqQnTpUb79P/r8KyHuIPkGIp1fHlq261BRmIH/1U/96jVwqb8lj8=',
                    'x-amz-meta-email': 'clive@email.co.uk',
                    'x-amz-meta-interviewer': 'OliverT',
                    'x-amz-meta-name': 'testclive',
                    'x-amz-request-id': '0X5K5SCPAJ4P8K5M'
                },
                'HTTPStatusCode': 200,
                'HostId': 'gF6gD3FeCTsssacCeCBtilYeqQnTpUb79P/r8KyHuIPkGIp1fHlq261BRmIH/1U/96jVwqb8lj8=',
                'RequestId': '0X5K5SCPAJ4P8K5M',
                'RetryAttempts': 0
            }
        },
        'expected_target_basename': None,
        'user_id': '8518c7ed-1df4-45e9-8dc4-d49b57ae0663',
    },
    # live interview; interviewer participating in 2 active projects; participant not taking part in active projects
    'dd2150f3-fec9-4ab3-90af-98d28a70d7f2/video/0002fe76-1a84-4039-8a52-795513cdd091.mp4': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 11854359,
            'ContentType': 'binary/octet-stream',
            'ETag': '"a2b75be34b503a47d07e3c2d1f73e2fe"',
            'LastModified': datetime.datetime(2020, 10, 23, 19, 57, 16, tzinfo=tzutc()),
            'Metadata': {
                'email': 'fred@email.co.uk',
                'interviewer': 'Karolina K'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '11854359',
                    'content-type': 'binary/octet-stream',
                    'date': 'Fri, 23 Oct 2020 20:01:29 GMT',
                    'etag': '"a2b75be34b503a47d07e3c2d1f73e2fe"',
                    'last-modified': 'Fri, 23 Oct 2020 '
                                     '19:57:16 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': 'HDadBg2R5DbXVyjuBp6TlpHNc/YFW2Sefu3uq0BR0HQCx20gVnGHDfhK3QKHeqq3CDafKlZaaHY=',
                    'x-amz-meta-email': 'fred@email.co.uk',
                    'x-amz-meta-interviewer': 'Karolina K',
                    'x-amz-request-id': '939FCEA57584653F'
                },
                'HTTPStatusCode': 200,
                'HostId': 'HDadBg2R5DbXVyjuBp6TlpHNc/YFW2Sefu3uq0BR0HQCx20gVnGHDfhK3QKHeqq3CDafKlZaaHY=',
                'RequestId': '939FCEA57584653F',
                'RetryAttempts': 0
            }
        },
        'expected_target_basename': None,
        'user_id': 'dceac123-03a7-4e29-ab5a-739e347b374d',
    },
    # live interview; interviewer and participant projects do not overlap
    '427ff1f2-f0cf-4719-a1cf-1a561c1ba496/video/8a1fdf5a-061b-41a6-bee9-36ac3fba3fee.mp4': {
        'head': {
            'AcceptRanges': 'bytes',
            'ContentLength': 11854359,
            'ContentType': 'binary/octet-stream',
            'ETag': '"a2b75be34b503a47d07e3c2d1f73e2fe"',
            'LastModified': datetime.datetime(2020, 10, 23, 22, 1, 36, tzinfo=tzutc()),
            'Metadata': {
                'email': 'eddie@email.co.uk',
                'interviewer': 'Karolina K'
            },
            'ResponseMetadata': {
                'HTTPHeaders': {
                    'accept-ranges': 'bytes',
                    'content-length': '11854359',
                    'content-type': 'binary/octet-stream',
                    'date': 'Fri, 23 Oct 2020 22:02:46 GMT',
                    'etag': '"a2b75be34b503a47d07e3c2d1f73e2fe"',
                    'last-modified': 'Fri, 23 Oct 2020 '
                                     '22:01:36 GMT',
                    'server': 'AmazonS3',
                    'x-amz-id-2': '96cEWduJhAS4+ptz2N0+oL8KZFcPmedpiSzxJpCGWjneKUksqOyUFAv0X8GTeBTOedQdofkWV0M=',
                    'x-amz-meta-email': 'eddie@email.co.uk',
                    'x-amz-meta-interviewer': 'Karolina K',
                    'x-amz-request-id': '443789E132A90F16'
                },
                'HTTPStatusCode': 200,
                'HostId': '96cEWduJhAS4+ptz2N0+oL8KZFcPmedpiSzxJpCGWjneKUksqOyUFAv0X8GTeBTOedQdofkWV0M=',
                'RequestId': '443789E132A90F16',
                'RetryAttempts': 0
            }
        },
        'expected_target_basename': None,
        'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515',
    },
}
