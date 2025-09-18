# This file is part of the Fairdata IDA research data storage service.
#
# Copyright (C) 2020 Ministry of Education and Culture, Finland
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
import os
import sys
import json
from tests.common.utils import *

class TestDataDeletion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("=== tests/datadeletion/test_datadeletion")

    def setUp(self):

        # load service configuration variables
        self.config = load_configuration()

        # keep track of success, for reference in tearDown
        self.success = False

        # timeout when waiting for actions to complete
        self.timeout = 10800 # 3 hours

        print("(initializing)")

        self.assertEqual(self.config["METAX_AVAILABLE"], 1)

        if self.config["METAX_API_VERSION"] >= 3:
            self.metax_headers = { 'Authorization': 'Token %s' % self.config["METAX_PASS"] }
        else:
            self.metax_user = (self.config["METAX_USER"], self.config["METAX_PASS"])

        flush_datasets(self)

        # empty trash data root of any residual project directories
        cmd = "sudo -u %s DEBUG=false %s/utils/appsupport/delete-ida-trash 0" % (self.config["HTTPD_USER"], self.config["ROOT"])
        result = os.system(cmd)

        # ensure we start with a fresh setup of projects, user accounts, and data
        cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts %s/tests/utils/triple-project.config" % (self.config["HTTPD_USER"], self.config["ROOT"], self.config["ROOT"])
        result = os.system(cmd)
        self.assertEqual(result, 0)

        # ensure all cache checksums have been generated for test_project_a (if OK, assume OK for all test projects)
        cmd = "sudo -u %s DEBUG=false %s/utils/appsupport/list-missing-checksums test_project_a" % (self.config["HTTPD_USER"], self.config["ROOT"])
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode(sys.stdout.encoding).strip()
            self.assertEqual(len(output), 0)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))

    def tearDown(self):
        # flush all test projects, user accounts, and data, but only if all tests passed,
        # else leave projects and data as-is so test project state can be inspected

        if self.success and self.config.get('NO_FLUSH_AFTER_TESTS', 'false') == 'false':

            print("(cleaning)")

            flush_datasets(self)

            cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts --flush %s/tests/utils/single-project.config" % (self.config["HTTPD_USER"], self.config["ROOT"], self.config["ROOT"])
            result = os.system(cmd)
            self.assertEqual(result, 0)

        self.assertTrue(self.success)

    def test_datadeletion(self):

        """
        Overview:

        1. The test projects and user accounts will be created and initialized as usual.

        2. Project A will have data frozen, and will have published datasets created in Metax.

        3. Project B will have frozen, but will have no published datasets.

        4. Project C will have no frozen data, and no datasets.

        5. Metax will be queried with various sets of input file PIDs to verify that the correct
           set of dataset PIDs are returned.

        6. Projects A, B, and C will be suspended and deleted and the correct deletion/preservation
           actions and email messages will be verified.
        """

        test_user_a = ("test_user_a", self.config["TEST_USER_PASS"])
        test_user_b = ("test_user_b", self.config["TEST_USER_PASS"])
        test_user_c = ("test_user_c", self.config["TEST_USER_PASS"])

        today = datetime.now().strftime("%Y-%m-%d")
        trash_root_base = "%s/%s" % (self.config["TRASH_DATA_ROOT"], today)

        data_root_project_a = "%s/PSO_test_project_a/files" % (self.config["STORAGE_OC_DATA_ROOT"])
        frozen_area_data_root_project_a = "%s/test_project_a" % (data_root_project_a)
        staging_area_data_root_project_a = "%s/test_project_a%s" % (data_root_project_a, self.config["STAGING_FOLDER_SUFFIX"])
        trash_root_project_a = "%s_test_project_a" % (trash_root_base)
        frozen_area_trash_root_project_a = "%s/test_project_a" % (trash_root_project_a)
        staging_area_trash_root_project_a = "%s/test_project_a%s" % (trash_root_project_a, self.config["STAGING_FOLDER_SUFFIX"])

        data_root_project_b = "%s/PSO_test_project_b/files" % (self.config["STORAGE_OC_DATA_ROOT"])
        frozen_area_data_root_project_b = "%s/test_project_b" % (data_root_project_b)
        staging_area_data_root_project_b = "%s/test_project_b%s" % (data_root_project_b, self.config["STAGING_FOLDER_SUFFIX"])
        trash_root_project_b = "%s_test_project_b" % (trash_root_base)
        frozen_area_trash_root_project_b = "%s/test_project_b" % (trash_root_project_b)
        staging_area_trash_root_project_b = "%s/test_project_b%s" % (trash_root_project_b, self.config["STAGING_FOLDER_SUFFIX"])

        data_root_project_c = "%s/PSO_test_project_c/files" % (self.config["STORAGE_OC_DATA_ROOT"])
        frozen_area_data_root_project_c = "%s/test_project_c" % (data_root_project_c)
        staging_area_data_root_project_c = "%s/test_project_c%s" % (data_root_project_c, self.config["STAGING_FOLDER_SUFFIX"])
        trash_root_project_c = "%s_test_project_c" % (trash_root_base)
        frozen_area_trash_root_project_c = "%s/test_project_c" % (trash_root_project_c)
        staging_area_trash_root_project_c = "%s/test_project_c%s" % (trash_root_project_c, self.config["STAGING_FOLDER_SUFFIX"])

        # --------------------------------------------------------------------------------

        print("Testing delete-closed-projects script with mock project lists (no side effects)")

        env = os.environ.copy()
        env["IDA_ENVIRONMENT"] = "TEST"
        env["MOCK_GRACE_PROJECTS"] = "mock_project_1\nmock_project_2\nmock_project_3\n"
        env["MOCK_DELETEDATA_PROJECTS"] = "mock_project_4\nmock_project_5\nmock_project_6\n"
        env["MOCK_SUSPENDED_PROJECTS"] = "mock_project_2\n"
        env["MOCK_INTERNAL_PROJECTS"] = "mock_project_3\nmock_project_5\n"
        env["MOCK_PUBLISHED_PROJECTS"] = "mock_project_6\n"

        cmd = [ "sudo", "-E", "-u", "apache", "%s/utils/appsupport/delete-closed-projects" % (self.config['ROOT']) ]

        try:
            output = subprocess.check_output(cmd, env=env, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertNotIn("Retrieving list of projects", output)
        self.assertIn("Project mock_project_1 should be suspended", output)
        self.assertIn("Project mock_project_2 is already suspended", output)
        self.assertIn("Project mock_project_3 is internal (skipped)", output)
        self.assertIn("Project mock_project_4 should be deleted", output)
        self.assertIn("Project mock_project_5 is internal (skipped)", output)
        self.assertIn("Project mock_project_6 should be preserved", output)
        
        # --------------------------------------------------------------------------------

        cmd_base = "sudo -u apache ECHO_TEST_EMAILS=\"true\" %s/utils/appsupport" % (self.config['ROOT'])

        print("Freezing project A folder /testdata/2017-08/Experiment_1")
        # Should be preserved after project removal, as part of published dataset
        data = { "project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1" }
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Freezing project A folder /testdata/2017-08/Experiment_2")
        # Should be preserved after project removal, as part of published dataset
        data = { "project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_2" }
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Freezing project A folder /testdata/2017-10/Experiment_3")
        # Should be preserved after project removal, as part of published dataset
        data = { "project": "test_project_a", "pathname": "/testdata/2017-10/Experiment_3" }
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Freezing project A folder /testdata/2017-10/Experiment_4")
        # Should be deleted after project removal, as not part of any published dataset
        data = { "project": "test_project_a", "pathname": "/testdata/2017-10/Experiment_4" }
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Retrieve project A frozen file details for all files associated with freeze action of folder /2017-10/Experiment_4")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        project_a_experiment_4_files = response.json()
        self.assertEqual(len(project_a_experiment_4_files), 12)

        print("Freezing project B folder /testdata/2017-11")
        # Should be deleted after project removal, as not part of any published dataset
        data = { "project": "test_project_b", "pathname": "/testdata/2017-11" }
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Creating Dataset 1 for project A containing all files in scope /testdata/2017-08/Experiment_1")
        dataset_data = DATASET_TEMPLATE_V3
        dataset_data['title'] = DATASET_TITLES[0]
        dataset_data['fileset'] = {
            "storage_service": "ida",
            "csc_project": "test_project_a",
            "directory_actions": [
                {
                    "action": "add",
                    "pathname": "/testdata/2017-08/Experiment_1/"
                }
            ]
        }
        response = requests.post("%s/datasets" % self.config['METAX_API'], headers=self.metax_headers, json=dataset_data)
        self.assertEqual(response.status_code, 201, response.text)
        dataset_1 = response.json()
        dataset_1_pid = dataset_1['id']

        print("Creating Dataset 2 for project A containing all files in scope /testdata/2017-08/Experiment_2")
        dataset_data = DATASET_TEMPLATE_V3
        dataset_data['title'] = DATASET_TITLES[1]
        dataset_data['fileset'] = {
            "storage_service": "ida",
            "csc_project": "test_project_a",
            "directory_actions": [
                {
                    "action": "add",
                    "pathname": "/testdata/2017-08/Experiment_2/"
                }
            ]
        }
        response = requests.post("%s/datasets" % self.config['METAX_API'], headers=self.metax_headers, json=dataset_data)
        self.assertEqual(response.status_code, 201, response.text)
        dataset_2 = response.json()
        dataset_2_pid = dataset_2['id']

        print("Creating Dataset 3 for project A containing all files in scope /testdata/2017-10/Experiment_3")
        dataset_data = DATASET_TEMPLATE_V3
        dataset_data['title'] = DATASET_TITLES[2]
        dataset_data['fileset'] = {
            "storage_service": "ida",
            "csc_project": "test_project_a",
            "directory_actions": [
                {
                    "action": "add",
                    "pathname": "/testdata/2017-10/Experiment_3/"
                }
            ]
        }
        response = requests.post("%s/datasets" % self.config['METAX_API'], headers=self.metax_headers, json=dataset_data)
        self.assertEqual(response.status_code, 201, response.text)
        dataset_3 = response.json()
        dataset_3_pid = dataset_3['id']

        print("Verify project A is identified as a published project, but not project B or project C")
        cmd = "%s/list-published-projects" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("test_project_a", output)
        self.assertNotIn("test_project_b", output)
        self.assertNotIn("test_project_c", output)

        print("Verify project A has published datasets")
        cmd = "%s/has-published-datasets test_project_a" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("true", output.strip())

        print("Verify project B has no published datasets")
        cmd = "%s/has-published-datasets test_project_b" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("false", output.strip())

        print("Verify project C has no published datasets")
        cmd = "%s/has-published-datasets test_project_c" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("false", output.strip())

        print("Verify project A has exactly 3 published datasets")
        cmd = "%s/list-published-datasets test_project_a --json" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        datasets = json.loads(output)
        self.assertEqual(3, len(datasets))

        cmd = "%s/list-published-datasets test_project_a" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn(dataset_1_pid, output)
        self.assertIn(dataset_2_pid, output)
        self.assertIn(dataset_3_pid, output)

        # --------------------------------------------------------------------------------

        print("Attempt to delete project A before suspending project (without --force parameter)")
        cmd = "%s/delete-project test_project_a" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            output = error.output.decode(sys.stdout.encoding)
            self.assertIn("The specified project test_project_a is not suspended", output)
            failed = True
        self.assertTrue(failed, output)

        print("Attempt to delete project B before suspending project (without --force parameter)")
        cmd = "%s/delete-project test_project_b" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            output = error.output.decode(sys.stdout.encoding)
            self.assertIn("The specified project test_project_b is not suspended", output)
            failed = True
        self.assertTrue(failed, output)

        print("Attempt to delete project C before suspending project (without --force parameter)")
        cmd = "%s/delete-project test_project_c" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            output = error.output.decode(sys.stdout.encoding)
            self.assertIn("The specified project test_project_c is not suspended", output)
            failed = True
        self.assertTrue(failed, output)

        print("Attempt to preserve project A before suspending project (without --force parameter)")
        cmd = "%s/preserve-project test_project_a" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            output = error.output.decode(sys.stdout.encoding)
            self.assertIn("The specified project test_project_a is not suspended", output)
            failed = True
        self.assertTrue(failed, output)

        print("Suspend (--delete) project A and verify correct email message sent")
        cmd = "%s/suspend-project test_project_a --delete" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_a, which has had rights to use the IDA service.", output)
        self.assertIn("The project is now SUSPENDED in and will be REMOVED from the IDA service in accordance with the official CSC Data Deletion Policy", output)
        self.assertIn("Access to the project space is now READ-ONLY.", output)
        self.assertIn("All unpublished project data will be DELETED from the IDA service during the final removal step following the official grace period.", output)
        self.assertIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, unless otherwise agreed.", output)
        self.assertNotIn("All project data will be DELETED from the IDA service during the final removal step following the official grace period.", output)

        print("Suspend (--delete) project B and verify correct email message sent")
        cmd = "%s/suspend-project test_project_b --delete" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_b, which has had rights to use the IDA service.", output)
        self.assertIn("The project is now SUSPENDED in and will be REMOVED from the IDA service in accordance with the official CSC Data Deletion Policy", output)
        self.assertIn("Access to the project space is now READ-ONLY.", output)
        self.assertIn("All project data will be DELETED from the IDA service during the final removal step following the official grace period.", output)
        self.assertNotIn("All unpublished project data will be DELETED from the IDA service during the final removal step following the official grace period.", output)
        self.assertNotIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, unless otherwise agreed.", output)

        print("Suspend (no --delete) project C and verify correct email message sent")
        cmd = "%s/suspend-project test_project_c" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_c, which has had rights to use the IDA service.", output)
        self.assertIn("The project is now SUSPENDED in the IDA service.", output)
        self.assertIn("Access to the project space is now READ-ONLY.", output)
        self.assertNotIn("The project is now SUSPENDED in and will be REMOVED from the IDA service in accordance with the official CSC Data Deletion Policy", output)
        self.assertNotIn("All project data will be DELETED from the IDA service during the final removal step following the official grace period.", output)
        self.assertNotIn("All unpublished project data will be DELETED from the IDA service during the final removal step following the official grace period.", output)
        self.assertNotIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, unless otherwise agreed.", output)

        print("Attempt to delete project A with invalid data deletion process state (without --force parameter)")
        cmd = "%s/delete-project test_project_a" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            failed = True
        self.assertTrue(failed, output)

        print("Attempt to preserve project A with invalid data deletion process state (without --force parameter)")
        cmd = "%s/preserve-project test_project_a" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            failed = True
        self.assertTrue(failed, output)

        # ---

        print("Preserve project A and verify preserved files, and correct email message sent")
        cmd = "%s/preserve-project test_project_a --force" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_a, which has had rights to use the IDA service.", output)
        self.assertIn("All unpublished project data has been DELETED from the IDA service.", output)
        self.assertIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, until otherwise agreed with the organization's IDA contact person.", output)
        self.assertNotIn("All project data has been DELETED from the IDA service.", output)

        print("Verify project A still exists in IDA/Nextcloud")
        cmd = "%s/project-status test_project_a" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertNotIn("Project test_project_a does not exist", output)

        print("Verify project A data for experiment 1 still remains in frozen area")
        cmd = "find %s/testdata/2017-08/Experiment_1 -type f | wc -l" % frozen_area_data_root_project_a
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("13", output.strip())

        print("Verify project A data for experiment 2 still remains in frozen area")
        cmd = "find %s/testdata/2017-08/Experiment_2 -type f | wc -l" % frozen_area_data_root_project_a
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("13", output.strip())

        print("Verify project A data for experiment 3 still remains in frozen area")
        cmd = "find %s/testdata/2017-10/Experiment_3 -type f | wc -l" % frozen_area_data_root_project_a
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("13", output.strip())

        print("Verify project A data for experiment 4 does not remain in frozen area")
        self.assertFalse(os.path.exists("%s/testdata/2017-10/Experiment_4" % frozen_area_data_root_project_a))

        print("Verify project A has no data remaining in staging area")
        self.assertFalse(os.path.exists("%s/testdata" % staging_area_data_root_project_a))

        print("Verify project A has no data from frozen experiment 1 in trash")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1" % frozen_area_trash_root_project_a))

        print("Verify project A has no data from frozen experiment 2 in trash")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_2" % frozen_area_trash_root_project_a))

        print("Verify project A has no data from frozen experiment 3 in trash")
        self.assertFalse(os.path.exists("%s/testdata/2017-10/Experiment_3" % frozen_area_trash_root_project_a))

        print("Verify project A data for frozen experiment 4 exists in trash")
        cmd = "find %s/testdata/2017-10/Experiment_4 -type f | wc -l" % frozen_area_trash_root_project_a
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("12", output.strip())

        print("Verify project A data from staging exists in trash")
        cmd = "find %s -type f | wc -l" % staging_area_trash_root_project_a
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("44", output.strip())

        print("Verify all project A datasets remain active (not deprecated) in Metax")
        cmd = "%s/list-published-datasets test_project_a --json" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        datasets = json.loads(output)
        self.assertEqual(3, len(datasets))

        cmd = "%s/list-published-datasets test_project_a" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn(dataset_1_pid, output)
        self.assertIn(dataset_2_pid, output)
        self.assertIn(dataset_3_pid, output)

        print("Verify project A is included in the list of datapreserved projects")
        cmd = "%s/list-datapreserved-projects --local" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("test_project_a", output)

        print("Verify PRESERVED sentinel file exists in data storage root of project A")
        self.assertTrue(os.path.exists("%s/PRESERVED" % data_root_project_a))

        print("Attempt to preserve already preserved project A")
        cmd = "%s/preserve-project test_project_a --force" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.assertIn("The specified project test_project_a is already preserved", error.output.decode(sys.stdout.encoding))
            failed = True
        self.assertTrue(failed, output)

        print("Verify project A status includes datapreserved state and published dataset listing")
        cmd = "%s/project-status test_project_a --json" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        status = json.loads(output)
        self.assertEqual(status.get("state"), "datapreserved", output)
        datasets = status.get("publishedDatasets", [])
        self.assertEqual(3, len(datasets))

        # ---

        print("Force delete project B and verify no preserved files, and correct email message sent")
        cmd = "%s/delete-project test_project_b --force" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_b, which has had rights to use the IDA service.", output)
        self.assertIn("All project data has been DELETED from the IDA service.", output)
        self.assertNotIn("All unpublished project data has been DELETED from the IDA service.", output)
        self.assertNotIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, until otherwise agreed with the organization's IDA contact person.", output)

        print("Verify project B no longer exists in IDA/Nextcloud")
        cmd = "%s/project-status test_project_b" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.assertIn("Project test_project_b does not exist", error.output.decode(sys.stdout.encoding))
            failed = True
        self.assertTrue(failed, output)

        print("Verify project B has no data remaining in IDA/Nextcloud")
        self.assertFalse(os.path.exists(data_root_project_b))

        print("Verify project B data exists in trash")
        cmd = "find %s -type f | wc -l" % trash_root_project_b
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("100", output.strip())

        # ---

        print("Force delete project C and verify no preserved files, and correct email message sent")
        cmd = "%s/delete-project test_project_c --force" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_c, which has had rights to use the IDA service.", output)
        self.assertIn("All project data has been DELETED from the IDA service.", output)
        self.assertNotIn("All unpublished project data has been DELETED from the IDA service.", output)
        self.assertNotIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, until otherwise agreed with the organization's IDA contact person.", output)

        print("Verify project C no longer exists in IDA/Nextcloud")
        cmd = "%s/project-status test_project_c" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.assertIn("Project test_project_c does not exist", error.output.decode(sys.stdout.encoding))
            failed = True
        self.assertTrue(failed, output)

        print("Verify project C has no data remaining in IDA/Nextcloud")
        self.assertFalse(os.path.exists(data_root_project_c))

        print("Verify project C data exists in trash")
        cmd = "find %s -type f | wc -l" % trash_root_project_c
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("100", output.strip())

        # ---

        print("Force delete project A and verify no preserved files, and correct email message sent")
        cmd = "%s/delete-project test_project_a --force" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertIn("You are a member of the CSC project test_project_a, which has had rights to use the IDA service.", output)
        self.assertIn("All project data has been DELETED from the IDA service.", output)
        self.assertNotIn("All unpublished project data has been DELETED from the IDA service.", output)
        self.assertNotIn("All published project data (included in one or more published datasets which are openly available, under embargo, or accessible to logged-in users through Etsin) will REMAIN in the IDA service to ensure long-term accessibility of the published datasets, until otherwise agreed with the organization's IDA contact person.", output)

        print("Verify project A no longer exists in IDA/Nextcloud")
        cmd = "%s/project-status test_project_a" % (cmd_base)
        failed = False
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.assertIn("Project test_project_a does not exist", error.output.decode(sys.stdout.encoding))
            failed = True
        self.assertTrue(failed, output)

        print("Verify project A has no data remaining in IDA/Nextcloud")
        self.assertFalse(os.path.exists(data_root_project_a))

        print("Verify project A data exists in trash")
        cmd = "find %s -type f | wc -l" % trash_root_project_a
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertEqual("104", output.strip())

        print("Verify project A is not included in the list of datapreserved projects")
        cmd = "%s/list-datapreserved-projects --local" % (cmd_base)
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(sys.stdout.encoding)
        except subprocess.CalledProcessError as error:
            self.fail(error.output.decode(sys.stdout.encoding))
        self.assertNotIn("test_project_a", output)

        # --------------------------------------------------------------------------------
        # If all tests passed, record success, in which case tearDown will be done

        self.success = True

        # --------------------------------------------------------------------------------
        # TODO: consider which tests may be missing...
