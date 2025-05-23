# --------------------------------------------------------------------------------
# This file is part of the Fairdata IDA research data storage service.
#
# Copyright (C) 2023 Ministry of Education and Culture, Finland
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
import time
import os
import sys
import json
from tests.common.utils import *


class TestChanges(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        print("=== tests/changes/test_changes")


    def setUp(self):

        # load service configuration variables
        self.config = load_configuration()

        # keep track of success, for reference in tearDown
        self.success = False

        # timeout when waiting for actions to complete
        self.timeout = 10800 # 3 hours

        self.assertEqual(self.config["METAX_AVAILABLE"], 1)

        print("(initializing)")

        # ensure we start with a fresh setup of projects, user accounts, and data
        cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts %s/tests/utils/single-project.config" % (self.config["HTTPD_USER"], self.config["ROOT"], self.config["ROOT"])
        result = os.system(cmd)
        self.assertEqual(result, 0)


    def tearDown(self):
        # flush all test projects, user accounts, and data, but only if all tests passed,
        # else leave projects and data as-is so test project state can be inspected

        if self.success and self.config.get('NO_FLUSH_AFTER_TESTS', 'false') == 'false':

            print("(cleaning)")

            cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts --flush %s/tests/utils/single-project.config" % (self.config["HTTPD_USER"], self.config["ROOT"], self.config["ROOT"])
            result = os.system(cmd)
            self.assertEqual(result, 0)

        self.assertTrue(self.success)


    def test_changes(self):

        """
        Overview:

        1. The test project A and user accounts will be created and initialized as usual.

        2. The oc_ida_data_changes table will be dropped and it will be verified that only
           a single migration epic event is reported for Project A.
           
        3. Project A will have a folder frozen, and the tests will wait until all postprocessing
           has completed such that all metadata is recorded in Metax.

        3. It will be verified that the last action reported will be for the freeze action.

        4. Various changes will be made via WebDAV to simulate changes made via the UI to ensure
           all data changes are recorded.

        5. Project A will be explicitly broken and then repaired to ensure repair related data changes
           are recorded.

        6. Various API requests will be made with various parameters to verify that the responses
           are correct.

        """

        admin_user = (self.config['NC_ADMIN_USER'], self.config['NC_ADMIN_PASS'])
        test_user_a = ('test_user_a', self.config['TEST_USER_PASS'])
        pso_user_a = ('PSO_test_project_a', self.config['PROJECT_USER_PASS'])
        not_a_user = ('not_a_user', 'not_a_password')

        # Generate timestamp to use for tests, sleep for 1 second first to ensure unique
        # from any initialization change timestamps
        time.sleep(1)
        self.config['START'] = generate_timestamp()

        # --------------------------------------------------------------------------------

        print("Attempt to retrieve initialization timestamp for non-existent project")
        response = requests.get("%s/dataChanges/not_a_project/init" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Unknown project.")

        print("Attempt to retrieve last change timestamp for non-existent project")
        response = requests.get("%s/dataChanges/not_a_project/last" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Unknown project.")

        print("Attempt to retrieve initialization timestamp for project with invalid credentials")
        response = requests.get("%s/dataChanges/test_project_a/init" % self.config["IDA_API"], auth=not_a_user, verify=False)
        self.assertEqual(response.status_code, 401)

        print("Attempt to retrieve last change timestamp for project with invalid credentials")
        response = requests.get("%s/dataChanges/test_project_a/last" % self.config["IDA_API"], auth=not_a_user, verify=False)
        self.assertEqual(response.status_code, 401)

        print("Attempt to report change with missing project parameter")
        data = {"user": "test_user_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"project\" not specified or is empty string")

        print("Attempt to report change with null project parameter")
        data = {"project": None, "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"project\" not specified or is empty string")

        print("Attempt to report change with empty string project parameter")
        data = {"project": "", "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"project\" not specified or is empty string")

        print("Attempt to report change with non-existent project")
        data = {"project": "not_a_project", "user": "test_user_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Unknown project.")

        print("Attempt to report change with missing user parameter")
        data = {"project": "test_project_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"user\" not specified or is empty string")

        print("Attempt to report change with null user parameter")
        data = {"project": "test_project_a", "user": None, "timestamp": self.config['START'], "change": "add", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"user\" not specified or is empty string")

        print("Attempt to report change with empty string user parameter")
        data = {"project": "test_project_a", "user": "", "timestamp": self.config['START'], "change": "add", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"user\" not specified or is empty string")

        print("Attempt to report change with invalid timestamp parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": "2023-01-01T01:01:01+03:00", "change": "add", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Specified timestamp \"2023-01-01T01:01:01+03:00\" is invalid")

        print("Attempt to report change with missing change parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"change\" not specified or is empty string")

        print("Attempt to report change with null change parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": None, "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"change\" not specified or is empty string")

        print("Attempt to report change with empty string change parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"change\" not specified or is empty string")

        print("Attempt to report change with invalid change parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "invalid", "pathname": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Invalid change specified.")

        print("Attempt to report change with missing pathname parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "move", "target": "/test_project_a/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"pathname\" not specified or is empty string")

        print("Attempt to report change with null pathname parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": None}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"pathname\" not specified or is empty string")

        print("Attempt to report change with empty string pathname parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": ""}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Required string parameter \"pathname\" not specified or is empty string")

        print("Attempt to report change with invalid pathname parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": "/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Pathname must begin with staging or frozen root folder")

        print("Attempt to report change with missing target parameter for move change")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a+/old/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Target must be specified.")

        print("Attempt to report change with null target parameter for copy change")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "copy", "pathname": "/test_project_a+/old/pathname", "target": None}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Target must be specified.")

        print("Attempt to report change with empty string target parameter for rename change")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "rename", "pathname": "/test_project_a+/old/pathname", "target": ""}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Target must be specified.")

        print("Attempt to report change with invalid target parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": "/test_project_a/old/pathname", "target": "/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Target must begin with staging or frozen root folder")

        print("Attempt to report change with invalid mode parameter")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "add", "pathname": "/test_project_a+/new/pathname", "mode": "invalid"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Invalid mode specified.")

        print("Attempt to report change with invalid credentials")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname", "mode": "cli"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=not_a_user, verify=False)
        self.assertEqual(response.status_code, 401)

        print("Attempt to report change with insufficient credentials")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname", "mode": "cli"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 403)

        # --------------------------------------------------------------------------------

        print("Query IDA for project initialization details")
        response = requests.get("%s/dataChanges/test_project_a/init" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        initDetails = response.json()
        self.assertIsNotNone(initDetails)
        self.assertEqual(initDetails.get('project'), 'test_project_a')
        self.assertNotEqual(initDetails.get('timestamp'), self.config["IDA_MIGRATION"])
        self.assertEqual(initDetails.get('user'), 'service')
        self.assertEqual(initDetails.get('change'), 'init')
        self.assertEqual(initDetails.get('pathname'), '/')
        self.assertIsNone(initDetails.get('target'))
        self.assertEqual(initDetails.get('mode'), 'system')

        print("Query IDA for last data change details")
        response = requests.get("%s/dataChanges/test_project_a/last" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertIsNotNone(change_details)
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertIsNotNone(change_details.get('timestamp'))
        self.assertNotEqual(change_details.get('timestamp'), self.config["IDA_MIGRATION"])
        self.assertIsNotNone(change_details.get('user'))
        self.assertIsNotNone(change_details.get('change'))
        self.assertIsNotNone(change_details.get('pathname'))
        self.assertIsNotNone(change_details.get('mode'))

        print("Query IDA for file inventory for project test_project_a and verify last change reported in inventory")
        response = requests.get("%s/inventory/test_project_a" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        inventory = response.json()
        self.assertEqual(inventory.get('project'), 'test_project_a')
        self.assertIsNotNone(inventory.get('created'))
        change_details = inventory.get('lastChange')
        self.assertIsNotNone(change_details)
        self.assertIsNone(change_details.get('project'))
        self.assertIsNotNone(change_details.get('timestamp'))
        self.assertNotEqual(change_details.get('timestamp'), self.config["IDA_MIGRATION"])
        self.assertIsNotNone(change_details.get('user'))
        self.assertIsNotNone(change_details.get('change'))
        self.assertIsNotNone(change_details.get('pathname'))
        self.assertIsNotNone(change_details.get('mode'))

        print("Report change with both timestamp and mode")
        data = {"project": "test_project_a", "user": "test_user_a", "timestamp": self.config['START'], "change": "move", "pathname": "/test_project_a/old/pathname", "target": "/test_project_a/new/pathname", "mode": "cli"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertIsNotNone(change_details)
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertEqual(change_details.get('timestamp'), self.config['START'])
        self.assertEqual(change_details.get('change'), 'move')
        self.assertEqual(change_details.get('pathname'), '/test_project_a/old/pathname')
        self.assertEqual(change_details.get('target'), '/test_project_a/new/pathname')
        self.assertEqual(change_details.get('mode'), 'cli')

        print("Query IDA for last recorded data change and verify last change matches just reported change")
        response = requests.get("%s/dataChanges/test_project_a/last" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertIsNotNone(change_details)
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertEqual(change_details.get('timestamp'), self.config['START'])
        self.assertEqual(change_details.get('change'), 'move')
        self.assertEqual(change_details.get('pathname'), '/test_project_a/old/pathname')
        self.assertEqual(change_details.get('target'), '/test_project_a/new/pathname')
        self.assertEqual(change_details.get('mode'), 'cli')

        print("Report change without either timestamp or mode")
        data = {"project": "test_project_a", "user": "test_user_a", "change": "copy", "pathname": "/test_project_a+/old/pathname", "target": "/test_project_a+/new/pathname"}
        response = requests.post("%s/dataChanges" % self.config["IDA_API"], json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertIsNotNone(change_details)
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertIsNotNone(change_details.get('timestamp'))
        self.assertTrue(change_details.get('timestamp') > self.config['START'])
        self.assertEqual(change_details.get('change'), 'copy')
        self.assertEqual(change_details.get('pathname'), '/test_project_a+/old/pathname')
        self.assertEqual(change_details.get('target'), '/test_project_a+/new/pathname')
        self.assertEqual(change_details.get('mode'), 'api')

        print("Query IDA for last recorded data change and verify last change matches just reported change")
        response = requests.get("%s/dataChanges/test_project_a/last" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertIsNotNone(change_details)
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertIsNotNone(change_details.get('timestamp'))
        self.assertTrue(change_details.get('timestamp') > self.config['START'])
        self.assertEqual(change_details.get('change'), 'copy')
        self.assertEqual(change_details.get('pathname'), '/test_project_a+/old/pathname')
        self.assertEqual(change_details.get('target'), '/test_project_a+/new/pathname')
        self.assertEqual(change_details.get('mode'), 'api')

        # --------------------------------------------------------------------------------

        print("Freezing folder /testdata/2017-08/Experiment_1")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Query IDA for last recorded data change and verify last recorded move change matches freeze action")
        response = requests.get("%s/dataChanges/test_project_a/last?change=move" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertEqual(change_details.get('change'), 'move')
        self.assertEqual(change_details.get('pathname'), '/test_project_a+/testdata/2017-08/Experiment_1')
        self.assertEqual(change_details.get('target'), '/test_project_a/testdata/2017-08/Experiment_1')
        self.assertEqual(change_details.get('mode'), 'api')
        self.assertTrue(change_details.get('timestamp') >= action_data.get('initiated'), "%s\n%s" % (json.dumps(change_details), json.dumps(action_data)))

        print("Unfreezing frozen file /testdata/2017-08/Experiment_1/test01.dat")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/test01.dat"}
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "unfreeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Query IDA for last recorded data change and verify last recorded move change matches unfreeze action")
        response = requests.get("%s/dataChanges/test_project_a/last?change=move" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertEqual(change_details.get('change'), 'move')
        self.assertEqual(change_details.get('pathname'), '/test_project_a/testdata/2017-08/Experiment_1/test01.dat')
        self.assertEqual(change_details.get('target'), '/test_project_a+/testdata/2017-08/Experiment_1/test01.dat')
        self.assertEqual(change_details.get('mode'), 'api')
        self.assertTrue(change_details.get('timestamp') >= action_data.get('initiated'), "%s\n%s" % (json.dumps(change_details), json.dumps(action_data)))

        print("Deleting frozen file /testdata/2017-08/Experiment_1/test02.dat")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/test02.dat"}
        response = requests.post("%s/delete" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["action"], "delete")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Query IDA for last recorded data change and verify last recorded delete change matches delete action")
        response = requests.get("%s/dataChanges/test_project_a/last?change=delete" % self.config["IDA_API"], auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        change_details = response.json()
        self.assertEqual(change_details.get('project'), 'test_project_a')
        self.assertEqual(change_details.get('user'), 'test_user_a')
        self.assertEqual(change_details.get('change'), 'delete')
        self.assertEqual(change_details.get('pathname'), '/test_project_a/testdata/2017-08/Experiment_1/test02.dat')
        self.assertIsNone(change_details.get('target'))
        self.assertEqual(change_details.get('mode'), 'api')
        self.assertTrue(change_details.get('timestamp') >= action_data.get('initiated'), "%s\n%s" % (json.dumps(change_details), json.dumps(action_data)))

        # --------------------------------------------------------------------------------
        # NOTE: Comprehensive add/copy/move/rename/delete changes are covered by the 
        #       command line tool automated behavioral tests
        # --------------------------------------------------------------------------------

        # If all tests passed, record success, in which case tearDown will be done

        self.success = True

        # --------------------------------------------------------------------------------
        # TODO: consider which tests may be missing...
