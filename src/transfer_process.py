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
# import hashlib
import os
import pysftp

import common.utilities as utils
from common.s3_utilities import S3Client
# from local.secrets import SDHS_CREDENTIALS  # replace this by SecretsManager

# def get_object_from_s3(s3_bucket_name, object_key, region=None, correlation_id=None):
#     if region is None:
#         region = utils.DEFAULT_AWS_REGION
#     s3_client = S3Client()
#     obj_http_path = f"http://s3.console.aws.amazon.com/s3/object/{s3_bucket_name}/{object_key}?region={region}"
#     obj = s3_client.get_object(bucket=s3_bucket_name, key=object_key)


# def get_md5(filename):
#     """
#     From: https://gist.github.com/nateware/4735384
#
#     Note: file is read in chunks to prevent exceeding system memory
#     """
#     f = open(filename, 'rb')
#     m = hashlib.md5()
#     while True:
#         data = f.read(10240)
#         if len(data) == 0:
#             break
#         m.update(data)
#     return m.hexdigest()


@utils.lambda_wrapper
def transfer_files(event, context):
    logger = event['logger']
    s3_bucket_name = utils.get_secret("incoming-interviews-bucket")['name']
    sdhs_credentials = utils.get_secret("sdhs-connection")
    sdhs_credentials['port'] = int(sdhs_credentials['port'])
    s3_client = S3Client()
    s3_files = s3_client.list_objects(s3_bucket_name)['Contents']
    transferred_files = list()
    skipped_files = list()
    with pysftp.Connection(**sdhs_credentials) as sftp:
        sftp.chdir('ftpuser')  # comment this out when finished with testing
        for f in s3_files:
            logger.debug('Working with s3 object', extra={'f': f})
            s3_path = f['Key']
            # s3_etag = f['ETag']
            s3_size = f['Size']
            s3_dirs, s3_filename = os.path.split(s3_path)
            logger.debug('Path of s3_obj', extra={'s3_dirs': s3_dirs, 's3_filename': s3_filename})
            sftp.makedirs(s3_dirs)
            if s3_dirs:
                with sftp.cd(s3_dirs):
                    copy_file = False
                    if s3_filename not in sftp.listdir():
                        copy_file = True
                    else:
                        if sftp.sftp_client.stat(s3_filename).st_size == s3_size:
                            logger.debug('File already exists in SDHS. Skipped', extra={'s3_path': s3_path,
                                                                                        'file_attributes': sftp.sftp_client.stat(s3_filename),
                                                                                        's3_size': s3_size})
                            skipped_files.append(s3_path)
                        else:
                            logger.debug('Size difference detected. Copying file again.', extra={'s3_path': s3_path,
                                                                                                    'file_attributes': sftp.sftp_client.stat(s3_filename),
                                                                                        's3_size': s3_size})
                            copy_file = True
                    if copy_file:
                        with sftp.sftp_client.open(s3_filename, 'wb') as sdhs_f:
                            s3_client.download_fileobj(s3_bucket_name, s3_path, sdhs_f)
                        transferred_files.append(s3_path)
    logger.info(f'Operation complete: {len(transferred_files)} files were transferred; {len(skipped_files)} were skipped', extra={
        'transferred_files': transferred_files,
        'skipped_files': skipped_files,
    })


if __name__ == "__main__":
    transfer_files(dict(), None)