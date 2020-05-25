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
import paramiko
import pysftp

from base64 import decodebytes

import common.utilities as utils
from common.s3_utilities import S3Client


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


class Interview:

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.audio_files = list()
        self.video_files = list()


@utils.lambda_wrapper
def archive_files(event, context):
    logger = event['logger']
    s3_bucket_name = utils.get_secret("incoming-interviews-bucket")['name']

    s3_client = S3Client()
    s3_files = s3_client.list_objects(s3_bucket_name)['Contents']

    interviews = dict()

    for f in s3_files:
        logger.debug('Working with s3 object', extra={'f': f})
        s3_path = f['Key']
        # s3_etag = f['ETag']
        s3_size = f['Size']
        s3_dirs, s3_filename = os.path.split(s3_path)
        interview_root_dir = s3_dirs.split('/')[0]
        interview = interviews.get(interview_root_dir)
        if interview is None:
            interviews[interview_root_dir]



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


@utils.lambda_wrapper
def transfer_files(event, context):
    logger = event['logger']
    s3_bucket_name = utils.get_secret("incoming-interviews-bucket")['name']
    sdhs_credentials = utils.get_secret("sdhs-connection")
    sdhs_credentials['port'] = int(sdhs_credentials['port'])

    # add host key to connection options
    host_key_str = sdhs_credentials['hostkey']
    host_key_bytes = bytes(host_key_str, encoding='utf-8')
    host_key = paramiko.ECDSAKey(data=decodebytes(host_key_bytes))  # or use paramiko.RSAKey for rsa keys
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys.add(sdhs_credentials['host'], sdhs_credentials['hostkey_type'], host_key)
    del sdhs_credentials['hostkey']
    del sdhs_credentials['hostkey_type']

    s3_client = S3Client()
    s3_files = s3_client.list_objects(s3_bucket_name)['Contents']

    transferred_files = list()
    skipped_files = list()

    with pysftp.Connection(**sdhs_credentials, cnopts=cnopts) as sftp:
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
