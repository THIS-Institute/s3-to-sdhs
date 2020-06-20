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
from http import HTTPStatus
import common.utilities as utils
from common.dynamodb_utilities import STACK_NAME


ENDPOINT_SECRET_NAME = "media-convert-endpoint"


class MediaConvertClient(utils.BaseClient):

    def __init__(self, profile_name=None, endpoint_url='default'):
        if endpoint_url is None:
            super().__init__('mediaconvert', profile_name=profile_name)
        elif endpoint_url == 'default':
            secret_endpoint_url = utils.get_secret(ENDPOINT_SECRET_NAME)['Url']
            super().__init__('mediaconvert', profile_name=profile_name, endpoint_url=secret_endpoint_url)
        else:
            super().__init__('mediaconvert', profile_name=profile_name, endpoint_url=endpoint_url)
        self.sm_client = None

    def describe_endpoints(self, **kwargs):
        """
        This is an one-off use method to get your account MediaConvert API endpoint and store it in
        SecretsManager

        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mediaconvert.html#MediaConvert.Client.describe_endpoints
        """
        response = self.client.describe_endpoints(**kwargs)
        assert response['ResponseMetadata']['HTTPStatusCode'] == HTTPStatus.OK, f"Call to describe_endpoints failed with response: {response}"
        first_endpoint = response['Endpoints'][0]
        if self.sm_client is None:
            self.sm_client = utils.SecretsManager()
        self.sm_client.create_or_update_secret(ENDPOINT_SECRET_NAME, first_endpoint)

    def create_audio_extraction_job(self, input_file_s3_key, **kwargs):
        aws_account_number = utils.get_secret('aws-account')['number']
        # todo: add role creation to CF template
        response = self.client.create_job(
            Role=f"arn:aws:iam::{aws_account_number}:role/MediaConvert_Default_Role",
            Settings={
                "OutputGroups": [
                    {
                        "Name": "File Group",
                        "Outputs": [
                            {
                                "ContainerSettings": {
                                    "Container": "RAW"
                                },
                                "AudioDescriptions": [
                                    {
                                        "AudioTypeControl": "FOLLOW_INPUT",
                                        "AudioSourceName": "Audio Selector 1",
                                        "CodecSettings": {
                                            "Codec": "MP3",
                                            "Mp3Settings": {
                                                "Bitrate": 192000,
                                                "Channels": 2,
                                                "RateControlMode": "CBR",
                                                "SampleRate": 48000
                                            }
                                        },
                                        "LanguageCodeControl": "FOLLOW_INPUT"
                                    }
                                ]
                            }
                        ],
                        "OutputGroupSettings": {
                            "Type": "FILE_GROUP_SETTINGS",
                            "FileGroupSettings": {
                                "Destination": f"s3://{STACK_NAME}-interview-audio/$fn$"
                            }
                        }
                    }
                ],
                "AdAvailOffset": 0,
                "Inputs": [
                    {
                        "AudioSelectors": {
                            "Audio Selector 1": {
                                "Offset": 0,
                                "DefaultSelection": "DEFAULT",
                                "ProgramSelection": 1
                            }
                        },
                        "FilterEnable": "AUTO",
                        "PsiControl": "USE_PSI",
                        "FilterStrength": 0,
                        "DeblockFilter": "DISABLED",
                        "DenoiseFilter": "DISABLED",
                        "TimecodeSource": "EMBEDDED",
                        "FileInput": f"s3://{input_file_s3_key}"
                    }
                ]
            },
            StatusUpdateInterval="SECONDS_60",
            **kwargs
        )
        from pprint import pprint
        pprint(response)




if __name__ == '__main__':
    mediaconvert_client = MediaConvertClient(endpoint_url=None)
    mediaconvert_client.describe_endpoints()
