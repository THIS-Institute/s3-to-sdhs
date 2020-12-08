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
import os
import paramiko
import pysftp
import thiscovery_lib.utilities as utils
from base64 import decodebytes


def get_sftp_parameters(project_acronym, correlation_id=None):
    sdhs_secret = utils.get_secret("sdhs-connection")
    project_params = sdhs_secret['project_specific_parameters'].get(project_acronym)
    if project_params is None:
        raise utils.ObjectDoesNotExistError(f'Could not find SDHS parameters for project', details={
            'project_acronym': project_acronym,
            'correlation_id': correlation_id
        })
    target_folder = project_params['folder']
    sdhs_params = dict()
    for param_name in ['host', 'port', 'hostkey', 'hostkey_type', 'username', 'password']:
        param_value = project_params.get(param_name)
        if param_value:
            sdhs_params[param_name] = param_value
        else:
            sdhs_params[param_name] = sdhs_secret.get(param_name)

    sdhs_params['port'] = int(sdhs_params['port'])
    # add host key to connection options
    host_key_str = sdhs_params['hostkey']
    host_key_bytes = bytes(host_key_str, encoding='utf-8')
    key_type = sdhs_params['hostkey_type']
    if key_type == 'ecdsa-sha2-nistp256':
        host_key = paramiko.ECDSAKey(data=decodebytes(host_key_bytes))
    elif key_type == 'ssh-rsa':
        host_key = paramiko.RSAKey(data=decodebytes(host_key_bytes))
    else:
        raise NotImplementedError(f'hostkey_type {key_type} not supported')
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys.add(sdhs_params['host'], sdhs_params['hostkey_type'], host_key)
    del sdhs_params['hostkey']
    del sdhs_params['hostkey_type']
    return sdhs_params, target_folder, cnopts


def parse_s3_path(s3_path):
    s3_dirs, s3_filename = os.path.split(s3_path)
    interview_dir, file_type = s3_dirs.split('/')[-2:]
    return s3_filename, interview_dir, file_type
