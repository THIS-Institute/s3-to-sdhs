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
import thiscovery_lib.utilities as utils
import unittest
from http import HTTPStatus
from pprint import pprint
from thiscovery_lib.core_api_utilities import CoreApiClient

import src.participants as p
import tests.testing_utilities as test_utils


class TestParticipants(test_utils.SdhsTransferTestCase):
    test_project_id = '183c23a1-76a7-46c3-8277-501f0740939d'  # PSFU-07
    expected_users = [
        {'anon_project_specific_user_id': '1406c523-6d12-4510-a745-271ddd9ad3e2',
         'email': 'eddie@email.co.uk',
         'first_name': 'Eddie',
         'last_name': 'Eagleton',
         'project_id': '183c23a1-76a7-46c3-8277-501f0740939d',
         'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515'},
        {'anon_project_specific_user_id': '2c8bba57-58a9-4ac7-98e8-beb34f0692c1',
         'email': 'altha@email.co.uk',
         'first_name': 'Altha',
         'last_name': 'Alcorn',
         'project_id': '183c23a1-76a7-46c3-8277-501f0740939d',
         'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'},
        {'anon_project_specific_user_id': '82ca200e-66d6-455d-95bc-617f974bcb26',
         'email': 'clive@email.co.uk',
         'first_name': 'Clive',
         'last_name': 'Cresswell',
         'project_id': '183c23a1-76a7-46c3-8277-501f0740939d',
         'user_id': '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'}
    ]

    def test_01_get_users_ok(self):
        pp = p.ProjectParser(
            project_acronym='PSFU-07',
            project_id=self.test_project_id,
            filename_prefix='PSFU-07-file'
        )
        self.assertCountEqual(self.expected_users, pp._get_users())

    def test_02_ParticipantInfoTransferManager_init_ok(self):
        pitm = p.ParticipantInfoTransferManager()
        expected_projects_to_process_ids = ['7c18c259-ace6-4f48-9206-93cd15501348']
        self.assertCountEqual(expected_projects_to_process_ids, [x.get('project_id') for x in pitm.projects_to_process])

    def test_03_transfer_participant_csv_ok(self):
        project_acronym = 'unittest-1'
        pp = p.ProjectParser(
            project_acronym=project_acronym,
            project_id=self.test_projects[project_acronym]['project_id'],
            filename_prefix=self.test_projects[project_acronym]['filename_prefix']
        )
        result = pp.transfer_participant_csv()
        self.assertEqual(HTTPStatus.OK, result)

    def test_04_parse_project_participants_ok(self):
        project_acronym = 'unittest-1'
        lambda_event = {
            'project_acronym': project_acronym,
            'project_id': self.test_projects[project_acronym]['project_id'],
            'filename_prefix': self.test_projects[project_acronym]['filename_prefix'],
            'core_api_client': CoreApiClient(),
        }
        result = p.parse_project_participants(lambda_event, None)
        self.assertEqual(HTTPStatus.OK, result)

    @unittest.skipUnless(os.environ['TEST_ON_AWS'] == 'True', 'Invokes lambda on AWS')
    def test_05_participants_to_sdhs_ok(self):
        result = p.participants_to_sdhs(dict(), None)
        self.assertEqual(1, len(result))
        self.assertEqual(HTTPStatus.ACCEPTED, result[0]['StatusCode'])

