# --------------------------------------------------------------------------------
# This file is part of the Fairdata IDA research data storage service.
#
# Copyright (C) 2026 Ministry of Education and Culture, Finland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# @author   CSC - IT Center for Science Ltd., Espoo Finland <servicedesk@csc.fi>
# @license  GNU Affero General Public License, version 3
# @link     https://www.fairdata.fi/en/ida
# --------------------------------------------------------------------------------
# Note regarding sequence of tests: this test case contains only a single test
# method, which utilizes the test projects, user accounts, and project data
# initialized during setup, such that the sequential actions in the single
# test method create side effects which subsequent actions and assertions may
# depend on. The state of the test accounts and data must be taken into account
# whenever adding tests at any particular point in that execution sequence.
# --------------------------------------------------------------------------------

import requests
import unittest
from datetime import date, timedelta
import os
from tests.common.utils import *


class TestIdaApp(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        print("=== tests/nextcloud/test_virusscan")


    def setUp(self):
        # load service configuration variables
        self.config = load_configuration()

        # keep track of success, for reference in tearDown
        self.success = False

        # timeout when waiting for actions to complete
        self.timeout = 10800 # 3 hours

        print("(initializing)")

        # dynamically download EICAR test content

        print("Retrieving EICAR virus scanning test file ...")
        eicar_url = "https://www.eicar.org/download/eicar.com.txt"
        self.eicar_data = None
        try:
            #raise Exception("BOOM")
            eicar_response = requests.get(eicar_url, timeout=90)
            eicar_response.raise_for_status()
            self.eicar_data = eicar_response.content
            print(f"EICAR: {self.eicar_data}")
        except BaseException as e:
            print(f"WARNING: Skipping virus scanning tests: Failed to download EICAR file ({e})")

        # Only need to initialize test accounts if retrieval of EICAR data succeeded
        if self.eicar_data:

            # ensure we start with a fresh setup of projects, user accounts, and data
            cmd = "DEBUG=false %s/tests/utils/initialize-test-accounts %s/tests/utils/single-project.config" % (self.config["ROOT"], self.config["ROOT"])
            result = os.system(cmd)
            self.assertEqual(result, 0)


    def tearDown(self):

        # Only need to flush if retrieval of EICAR data succeeded, as otherwise no accounts were initialized
        if self.eicar_data:

            # flush all test projects, user accounts, and data, but only if all tests passed,
            # else leave projects and data as-is so test project state can be inspected

            if self.success and self.config.get('NO_FLUSH_AFTER_TESTS', 'false') == 'false':
                print("(cleaning)")
                cmd = "DEBUG=false %s/tests/utils/initialize-test-accounts --flush" % self.config["ROOT"]
                os.system(cmd)

        # verify all executed tests passed

        self.assertTrue(self.success)


    def test_virusscan(self):

        if not self.eicar_data:
            self.success = True
            return

        test_user_a = ("test_user_a", self.config["TEST_USER_PASS"])

        frozen_area_root = "%s/PSO_test_project_a/files/test_project_a" % (self.config["STORAGE_OC_DATA_ROOT"])
        staging_area_root = "%s/PSO_test_project_a/files/test_project_a%s" % (self.config["STORAGE_OC_DATA_ROOT"], self.config["STAGING_FOLDER_SUFFIX"])

        # --------------------------------------------------------------------------------

        print("--- Virus Scanning")

        print("Upload infected test file")
        url = "%s/test_user_a/test_project_a+/eicar.txt" % self.config["FILE_API"]
        response = requests.put(url=url, data=self.eicar_data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 201)

        self.assertTrue(os.path.exists("%s/eicar.txt" % (staging_area_root)))

        print("Attempt to freeze infected file")
        data = {"project": "test_project_a", "pathname": "/eicar.txt"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        print("Verify file was physically moved from staging to frozen area")
        self.assertFalse(os.path.exists("%s/eicar.txt" % (staging_area_root)))
        self.assertTrue(os.path.exists("%s/eicar.txt" % (frozen_area_root)))

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a, should_be_failed = True)

        # --------------------------------------------------------------------------------
        # If all tests passed, record success, in which case tearDown will be done

        self.success = True

        # --------------------------------------------------------------------------------

        # TODO: consider which tests may be missing...
