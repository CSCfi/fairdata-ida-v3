# --------------------------------------------------------------------------------
# This file is part of the Fairdata IDA research data storage service.
#
# Copyright (C) 2018 Ministry of Education and Culture, Finland
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
        print("=== tests/nextcloud/test_ida_app")


    def setUp(self):
        # load service configuration variables
        self.config = load_configuration()

        # keep track of success, for reference in tearDown
        self.success = False

        # timeout when waiting for actions to complete
        self.timeout = 10800 # 3 hours

        print("(initializing)")

        self.ida_project = "sudo -u %s DEBUG=false %s/admin/ida_project" % (self.config['HTTPD_USER'], self.config['ROOT'])
        self.suspendedSentinelFile = "%s/control/SUSPENDED" % self.config["STORAGE_OC_DATA_ROOT"]

        # ensure service is not suspended

        if (os.path.exists(self.suspendedSentinelFile)):
            os.remove(self.suspendedSentinelFile)
        self.assertFalse(os.path.exists(self.suspendedSentinelFile))

        # ensure we start with a fresh setup of projects, user accounts, and data

        cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts" % (self.config["HTTPD_USER"], self.config["ROOT"])
        result = os.system(cmd)
        self.assertEqual(result, 0)

        cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-max-files test_project_a" % (self.config["HTTPD_USER"], self.config["ROOT"])
        result = os.system(cmd)
        self.assertEqual(result, 0)

        cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-max-files test_project_b" % (self.config["HTTPD_USER"], self.config["ROOT"])
        result = os.system(cmd)
        self.assertEqual(result, 0)

        self.ida_project = "sudo -u %s DEBUG=false %s/admin/ida_project" % (self.config['HTTPD_USER'], self.config['ROOT'])


    def tearDown(self):

        # ensure service is not suspended

        if (os.path.exists(self.suspendedSentinelFile)):
            os.remove(self.suspendedSentinelFile)
        self.assertFalse(os.path.exists(self.suspendedSentinelFile))

        # flush all test projects, user accounts, and data, but only if all tests passed,
        # else leave projects and data as-is so test project state can be inspected

        if self.success and self.config.get('NO_FLUSH_AFTER_TESTS', 'false') == 'false':
            print("(cleaning)")
            cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts --flush" % (self.config["HTTPD_USER"], self.config["ROOT"])
            os.system(cmd)

        # verify all tests passed

        self.assertTrue(self.success)


    def test_ida_app(self):

        admin_user = (self.config["NC_ADMIN_USER"], self.config["NC_ADMIN_PASS"])
        pso_user_a = (self.config["PROJECT_USER_PREFIX"] + "test_project_a", self.config["PROJECT_USER_PASS"])
        pso_user_b = (self.config["PROJECT_USER_PREFIX"] + "test_project_b", self.config["PROJECT_USER_PASS"])
        pso_user_c = (self.config["PROJECT_USER_PREFIX"] + "test_project_c", self.config["PROJECT_USER_PASS"])
        pso_user_d = (self.config["PROJECT_USER_PREFIX"] + "test_project_d", self.config["PROJECT_USER_PASS"])
        test_user_a = ("test_user_a", self.config["TEST_USER_PASS"])
        test_user_b = ("test_user_b", self.config["TEST_USER_PASS"])
        test_user_c = ("test_user_c", self.config["TEST_USER_PASS"])
        test_user_d = ("test_user_d", self.config["TEST_USER_PASS"])
        test_user_x = ("test_user_x", self.config["TEST_USER_PASS"])
        test_user_s = ("test_user_s", self.config["TEST_USER_PASS"])

        frozen_area_root = "%s/PSO_test_project_a/files/test_project_a" % (self.config["STORAGE_OC_DATA_ROOT"])
        staging_area_root = "%s/PSO_test_project_a/files/test_project_a%s" % (self.config["STORAGE_OC_DATA_ROOT"], self.config["STAGING_FOLDER_SUFFIX"])

        # --------------------------------------------------------------------------------

        print("--- Project Titles")

        title = "Test+Project+Title"

        print("Attempt to define project title with missing project parameter")
        response = requests.post("%s/setProjectTitle?title=%s" % (self.config["IDA_API"], title), auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 400, response.text)
        action_data = response.json()
        self.assertEqual('Required string parameter "project" not specified or is empty string', action_data.get('message'))

        print("Attempt to define project title with missing title parameter")
        response = requests.post("%s/setProjectTitle?project=%s" % (self.config["IDA_API"], "test_project_a"), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400, response.text)
        action_data = response.json()
        self.assertEqual('Required string parameter "title" not specified or is empty string', action_data.get('message'))

        print("Attempt to define project title for non-existent project")
        response = requests.post("%s/setProjectTitle?project=%s&title=%s" % (self.config["IDA_API"], "nonexistentproject", title), auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 400, response.text)
        action_data = response.json()
        self.assertEqual('The specified project was not found.', action_data.get('message'))

        print("Attempt to define project title with insufficient privileges")
        response = requests.post("%s/setProjectTitle?project=%s&title=%s" % (self.config["IDA_API"], "test_project_a", title), auth=test_user_a, verify=False)
        action_data = response.json()
        self.assertEqual(response.status_code, 403, response.text)

        print("Define project title as PSO user")
        # Sometimes a mysterious error condition can occur when running the tests, which doesn't appear to ever occur
        # in production or manual testing, probably due to Nextcloud housekeeping lag, so if this fails, we try again
        try:
            response = requests.post("%s/setProjectTitle?project=%s&title=%s" % (self.config["IDA_API"], "test_project_a", title), auth=pso_user_a, verify=False)
            self.assertEqual(response.status_code, 200, response.text)
        except:
            print("(project title update as PSO user failed, retrying...)")
            time.sleep(10)
            response = requests.post("%s/setProjectTitle?project=%s&title=%s" % (self.config["IDA_API"], "test_project_a", title), auth=pso_user_a, verify=False)
            self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["message"], "Test Project Title")

        print("Define project title as admin user")
        # Sometimes a mysterious error condition can occur when running the tests, which doesn't appear to ever occur
        # in production or manual testing, probably due to Nextcloud housekeeping lag, so if this fails, we try again
        try:
            response = requests.post("%s/setProjectTitle?project=%s&title=%s" % (self.config["IDA_API"], "test_project_a", title), auth=admin_user, verify=False)
            self.assertEqual(response.status_code, 200, response.text)
        except:
            print("(project title update as admin failed, retrying...)")
            time.sleep(10)
            response = requests.post("%s/setProjectTitle?project=%s&title=%s" % (self.config["IDA_API"], "test_project_a", title), auth=admin_user, verify=False)
            self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["message"], "Test Project Title")

        print("Retrieve defined project title")
        response = requests.get("%s/getProjectTitle?project=%s" % (self.config["IDA_API"], "test_project_a"), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        # Sometimes a mysterious race condition can occur when running the tests, which doesn't appear to ever occur
        # in actual production use, where retrieval of the immediately created title via the API fails and defaults to the
        # project name, so we retry
        if (action_data["message"] == "test_project_a"):
            print("(project title retrieval failed, retrying...)")
            time.sleep(10)
            response = requests.get("%s/getProjectTitle?project=%s" % (self.config["IDA_API"], "test_project_a"), auth=test_user_a, verify=False)
            self.assertEqual(response.status_code, 200)
            action_data = response.json()
        self.assertEqual(action_data["message"], "Test Project Title")

        print("Retrieve default project title")
        response = requests.get("%s/getProjectTitle?project=%s" % (self.config["IDA_API"], "test_project_b"), auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200, response.text)
        action_data = response.json()
        self.assertEqual(action_data["message"], "test_project_b")

        print("Attempt to retrieve project title with missing project parameter")
        response = requests.get("%s/getProjectTitle" % (self.config["IDA_API"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400, response.text)
        action_data = response.json()
        self.assertEqual('Required string parameter "project" not specified or is empty string', action_data.get('message'))

        print("Attempt to retrieve project title with insufficient permissions")
        response = requests.get("%s/getProjectTitle?project=%s" % (self.config["IDA_API"], "test_project_a"), auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 403, response.text)
        action_data = response.json()
        self.assertEqual('Forbidden', action_data.get('message'))

        print("Attempt to retrieve title of non-existent project")
        response = requests.get("%s/getProjectTitle?project=%s" % (self.config["IDA_API"], "nonexistentproject"), auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 400, response.text)
        action_data = response.json()
        self.assertEqual('The specified project was not found.', action_data.get('message'))

        # --------------------------------------------------------------------------------

        print("--- Temporary Share Links")

        headers = { 'OCS-APIRequest': 'true' }

        print("Create temporary share link")
        tomorrow = date.today() + timedelta(days=1)
        expireDate = tomorrow.strftime("%Y-%m-%d")
        data = {
            "expireDate": expireDate,
            "hideDownload": "false",
            "password": "",
            "passwordChanged": "false",
            "sendPasswordByTalk": "false",
            "permissions": 1,
            "shareType": 3,
            "path": "/test_project_a+/testdata/2017-08/Experiment_1/test01.dat"
        }
        response = requests.post("%s?format=json" % self.config["SHARE_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        #print(response.text) # TEMP DEBUG
        ocs = response_data.get("ocs")
        self.assertIsNotNone(ocs)
        share_data = ocs.get("data")
        self.assertIsNotNone(share_data)
        token = share_data.get("token")
        self.assertIsNotNone(token)
        self.assertTrue(token.startswith("NOT-FOR-PUBLICATION-"))

        # --------------------------------------------------------------------------------

        print("--- WebDAV Access Limitations")

        print("Attempt to duplicate file to frozen area with COPY request to WebDAV API")
        url = "%s/test_user_d/test_project_d+/testdata/2017-11/Experiment_6/test01.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d/test01.dat" % self.config["FILE_API"] }
        response = requests.request(method='COPY', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to rename file to frozen area with MOVE request to WebDAV API")
        url = "%s/test_user_d/test_project_d+/testdata/2017-11/Experiment_6/test01.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d/test01.dat" % self.config["FILE_API"] }
        response = requests.request(method='MOVE', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to remove folder from frozen area with DELETE request to WebDAV API")
        url = "%s/test_user_d/test_project_d/testdata/empty_folder_f/x/y/z" % self.config["FILE_API"]
        response = requests.request(method='DELETE', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to remove root frozen folder with DELETE request to WebDAV API")
        url = "%s/test_user_d/test_project_d" % self.config["FILE_API"]
        response = requests.request(method='DELETE', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Root project folders cannot be modified by project users', response.text)

        self.assertTrue(make_ida_offline(self))

        print("Attempt to copy file in staging area with COPY request to WebDAV API while service is offline")
        url = "%s/test_user_d/test_project_d+/testdata/2017-11/Experiment_6/test03.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d+/test03.dat" % self.config["FILE_API"] }
        response = requests.request(method='COPY', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 503)
        self.assertIn('Service unavailable. Please try again later.', response.text)

        self.assertTrue(make_ida_online(self))

        print("Copy file in staging area with COPY request to WebDAV API while service is back online")
        url = "%s/test_user_d/test_project_d+/testdata/2017-11/Experiment_6/test01.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d+/test01.dat" % self.config["FILE_API"] }
        response = requests.request(method='COPY', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 201)

        #---

        print("(suspending service)")
        cmd = "sudo -u %s touch %s" % (self.config["HTTPD_USER"], self.suspendedSentinelFile)
        result = os.system(cmd)
        self.assertEqual(result, 0)

        #---

        print("Retrieve file contents with GET request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.get(url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Retrieve file details with PROPFIND request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.request(method='PROPFIND', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Retrieve folder details with PROPFIND request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/2017-10" % self.config["FILE_API"]
        response = requests.request(method='PROPFIND', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Attempt to upload new file contents with PUT request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/newfile1.txt" % self.config["FILE_API"]
        data = { 'foo': 'bar' }
        response = requests.put(url=url, data=data, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to remove file with DELETE request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.request(method='DELETE', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to create new folder with MKCOL request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/newfolder" % self.config["FILE_API"]
        response = requests.request(method='MKCOL', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to duplicate file with COPY request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test01.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test01.dat2" % self.config["FILE_API"] }
        response = requests.request(method='COPY', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to rename file with MOVE request to WebDAV API when service is suspended")
        url = "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test02.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test02.dat2" % self.config["FILE_API"] }
        response = requests.request(method='MOVE', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to change creation date of file with PROPPATCH request to WebDAV API when service is suspended")
        data = """<?xml version=\"1.0\"?>
                      <d:propertyupdate xmlns:d=\"DAV:\">
                         <d:set>
                             <d:prop>
                                 <creationdate>1966-03-31</creationdate>
                             </d:prop>
                         </d:set>
                      </d:propertyupdate>
        """
        headers = { 'ContentType': 'application/xml' }
        url = "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test03.dat" % self.config["FILE_API"]
        response = requests.request(method='PROPPATCH', url=url, data=data, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("(unsuspending service)")
        if (os.path.exists(self.suspendedSentinelFile)):
            os.remove(self.suspendedSentinelFile)
        self.assertFalse(os.path.exists(self.suspendedSentinelFile))

        print("Retrieve file contents with GET request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.get(url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Retrieve file details with PROPFIND request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.request(method='PROPFIND', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Retrieve folder details with PROPFIND request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/2017-10" % self.config["FILE_API"]
        response = requests.request(method='PROPFIND', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Upload new file contents with PUT request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/newfile1.txt" % self.config["FILE_API"]
        data = { 'foo': 'bar' }
        response = requests.put(url=url, data=data, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 201)

        print("Remove file with DELETE request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.request(method='DELETE', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 204)

        print("Create new folder with MKCOL request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/newfolder" % self.config["FILE_API"]
        response = requests.request(method='MKCOL', url=url, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 201)

        print("Duplicate file with COPY request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test01.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test01.dat2" % self.config["FILE_API"] }
        response = requests.request(method='COPY', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 201)

        print("Rename file with MOVE request to WebDAV API when project is not suspended")
        url = "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test02.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test02.dat2" % self.config["FILE_API"] }
        response = requests.request(method='MOVE', url=url, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 201)

        print("Change creation date of file with PROPPATCH request to WebDAV API when project is not suspended")
        data = """<?xml version=\"1.0\"?>
                      <d:propertyupdate xmlns:d=\"DAV:\">
                         <d:set>
                             <d:prop>
                                 <creationdate>1966-03-31</creationdate>
                             </d:prop>
                         </d:set>
                      </d:propertyupdate>
        """
        headers = { 'ContentType': 'application/xml' }
        url = "%s/test_user_d/test_project_d+/testdata/2017-10/Experiment_3/test03.dat" % self.config["FILE_API"]
        response = requests.request(method='PROPPATCH', url=url, data=data, headers=headers, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Retrieve file contents with GET request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.get(url=url, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Retrieve file details with PROPFIND request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.request(method='PROPFIND', url=url, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Retrieve folder details with PROPFIND request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/2017-10" % self.config["FILE_API"]
        response = requests.request(method='PROPFIND', url=url, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 207)

        print("Attempt to upload new file contents with PUT request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/newfile1.txt" % self.config["FILE_API"]
        data = { 'foo': 'bar' }
        response = requests.put(url=url, data=data, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to remove file with DELETE request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/License.txt" % self.config["FILE_API"]
        response = requests.request(method='DELETE', url=url, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to create new folder with MKCOL request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/newfolder" % self.config["FILE_API"]
        response = requests.request(method='MKCOL', url=url, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to duplicate file with COPY request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/2017-08/Experiment_1/test01.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_s+/testdata/2017-08/Experiment_1/test01.dat2" % self.config["FILE_API"] }
        response = requests.request(method='COPY', url=url, headers=headers, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to duplicate file with COPY request to WebDAV API when project is suspended")
        url = "%s/test_user_s/test_project_s+/testdata/2017-08/Experiment_1/test02.dat" % self.config["FILE_API"]
        headers = { "Destination": "%s/test_user_d/test_project_s+/testdata/2017-08/Experiment_1/test02.dat2" % self.config["FILE_API"] }
        response = requests.request(method='MOVE', url=url, headers=headers, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("Attempt to change creation date of file with PROPPATCH request to WebDAV API when project is suspended")
        data = """<?xml version=\"1.0\"?>
                      <d:propertyupdate xmlns:d=\"DAV:\">
                         <d:set>
                             <d:prop>
                                 <creationdate>1966-03-31</creationdate>
                             </d:prop>
                         </d:set>
                      </d:propertyupdate>
        """
        headers = { 'ContentType': 'application/xml' }
        url = "%s/test_user_s/test_project_s+/testdata/2017-08/Experiment_1/test03.dat" % self.config["FILE_API"]
        response = requests.request(method='PROPPATCH', url=url, data=data, headers=headers, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        # --------------------------------------------------------------------------------

        print("--- Offline Freezing Limitations")

        self.assertTrue(make_ida_offline(self))

        headers = { 'OCS-APIRequest': 'true' }

        data = {"project": "test_project_a", "pathname": "/testdata/License.txt"}

        print("Attempt to freeze a file when service is offline")
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 503)
        self.assertIn('Service unavailable. Please try again later.', response.text)

        self.assertTrue(make_ida_online(self))

        # --------------------------------------------------------------------------------

        print("--- Suspended Service and Project Freezing Limitations")

        print("(suspending service)")
        cmd = "sudo -u %s touch %s" % (self.config["HTTPD_USER"], self.suspendedSentinelFile)
        result = os.system(cmd)
        self.assertEqual(result, 0)

        headers = { 'OCS-APIRequest': 'true' }

        data = {"project": "test_project_a", "pathname": "/testdata/License.txt"}

        print("Attempt to freeze a file when all projects are suspended")
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        print("(unsuspending service)")
        if (os.path.exists(self.suspendedSentinelFile)):
            os.remove(self.suspendedSentinelFile)
        self.assertFalse(os.path.exists(self.suspendedSentinelFile))

        data = {"project": "test_project_s", "pathname": "/testdata/License.txt"}

        print("Attempt to freeze a file when the specific project is suspended")
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_s, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('Project suspended. Action not permitted.', response.text)

        # --------------------------------------------------------------------------------

        print("--- Freeze Actions")

        headers = { 'X-SIMULATE-AGENTS': 'true' }

        print("Freeze a single file")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/test01.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        # TODO: check that all mandatory fields are defined with valid values for action

        print("Verify file was physically moved from staging to frozen area")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (staging_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (frozen_area_root)))

        print("Retrieve details of all frozen files associated with previous action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 1)
        file_data = file_set_data[0]
        file_pid = file_data["pid"]
        self.assertEqual(file_data["project"], data["project"])
        self.assertEqual(file_data["action"], action_data["pid"])

        # TODO: check that all mandatory fields are defined with valid values for frozen file

        print("Retrieve frozen file details by pathname")
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pathname"], data["pathname"])
        self.assertEqual(file_data["pid"], file_pid)
        self.assertEqual(file_data["size"], 446)

        print("Retrieve frozen file details by PID")
        response = requests.get("%s/files/%s" % (self.config["IDA_API"], file_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data_2 = response.json()
        self.assertEqual(file_data_2["pid"], file_data["pid"])
        self.assertEqual(file_data_2["project"], file_data["project"])
        self.assertEqual(file_data_2["pathname"], file_data["pathname"])
        self.assertEqual(file_data["size"], 446)

        print("Freeze a folder")
        data["pathname"] = "/testdata/2017-08"
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        action_pid = action_data["pid"]
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Retrieve details of all frozen files associated with previous action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 26)
        # file count for this freeze folder action should never change, even if files are unfrozen/deleted
        # (store this action PID and verify after all unfreeze and delete actions that count has not changed)
        original_freeze_folder_action_pid = action_pid
        original_freeze_folder_action_file_count = 26

        print("Retrieve file details from hidden frozen file")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/.hidden_file"}
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_x_data = response.json()
        self.assertEqual(file_x_data.get('size'), 446)

        print("Attempt to freeze an empty folder")
        data["pathname"] = "/testdata/empty_folder_s"
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data.get('message'), "The specified folder contains no files which can be frozen.")

        print("Freeze a single file where filename contains special characters")
        data = {"project": "test_project_a", "pathname": "/testdata/Special Characters/$file with special characters #~;@-+'&!%^.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Retrieve frozen file details by pathname where filename contains special characters")
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pathname"], data["pathname"])
        self.assertEqual(file_data["size"], 446)

        # --------------------------------------------------------------------------------

        print("--- Unfreeze Actions")

        print("Unfreeze single frozen file")
        data["pathname"] = "/testdata/2017-08/Experiment_1/baseline/test01.dat"
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "unfreeze")
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        # TODO: check that all mandatory fields are defined with valid values for action

        print("Verify file was physically moved from frozen to staging area")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1/baseline/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_1/baseline/test01.dat" % (staging_area_root)))

        print("Retrieve details of all frozen files associated with previous action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 1)
        file_data = file_set_data[0]
        self.assertEqual(file_data["project"], data["project"])
        self.assertEqual(file_data["action"], action_data["pid"])

        # TODO: check that all mandatory fields are defined with valid values for unfrozen file (e.g. removed, etc.)

        print("Unfreeze a folder")
        data["pathname"] = "/testdata/2017-08/Experiment_1/baseline"
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "unfreeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Retrieve details of all unfrozen files associated with previous action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 5)

        print("Attempt to retrieve details of all unfrozen files associated with previous action as user without rights to project")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 0)

        print("Attempt to retrieve details of all unfrozen files associated with a non-existent action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], "NO_SUCH_PID"), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 0)

        print("Attempt to unfreeze an empty folder")
        data["pathname"] = "/testdata/empty_folder_f"
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data.get('message'), "The specified folder contains no files which can be unfrozen.")

        # --------------------------------------------------------------------------------

        print("--- Freeze Action File Validity Checks")

        system_pathname = "%s/testdata/2017-08/Experiment_1/baseline/test01.dat" % staging_area_root

        print("(modify the size of the test file on disk)")
        with open(system_pathname, "a") as file:
            file.write("more data")

        print("Attempt to freeze a file where the filesystem size is different from the size recorded in the Nextcloud cache")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/baseline/test01.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertIn(
            'File size on disk (455) does not match the originally reported upload file size (446) for file /test_project_a+/testdata/2017-08/Experiment_1/baseline/test01.dat',
            response_data.get('message')
        )

        print("(remove the test file from disk)")
        os.remove(system_pathname)

        print("Attempt to freeze a file which does not exist on disk but is recorded in the Nextcloud cache")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/baseline/test01.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertIn(
            'File not found on disk: /test_project_a+/testdata/2017-08/Experiment_1/baseline/test01.dat',
            response_data.get('message')
        )

        # --------------------------------------------------------------------------------

        print("--- Delete Actions")

        print("Delete single frozen file")
        data["pathname"] = "/testdata/2017-08/Experiment_1/test02.dat"
        response = requests.post("%s/delete" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "delete")
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        # TODO: check that all mandatory fields are defined with valid values for action

        print("Verify file was physically removed from frozen area")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1/test02.dat" % (frozen_area_root)))

        print("Retrieve details of all deleted files associated with previous action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 1)
        file_data = file_set_data[0]
        self.assertEqual(file_data["project"], data["project"])
        self.assertEqual(file_data["action"], action_data["pid"])
        self.assertIsNotNone(file_data.get("removed"))

        # TODO: check that all mandatory fields are defined with valid values for unfrozen file

        print("Delete a frozen folder")
        data["pathname"] = "/testdata/2017-08/Experiment_1"
        response = requests.post("%s/delete" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "delete")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Verify folder was physically removed from frozen area")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1" % (frozen_area_root)))

        print("Retrieve details of all deleted files associated with previous action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), 6)

        print("Verify file count has not changed for original freeze folder action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], original_freeze_folder_action_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), original_freeze_folder_action_file_count)

        print("Delete a frozen folder with no files within folder scope")
        data["pathname"] = "/testdata/empty_folder_f"
        response = requests.post("%s/delete" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "delete")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Verify folder was physically removed from frozen area")
        self.assertFalse(os.path.exists("%s/testdata/empty_folder_f" % (frozen_area_root)))

        # --------------------------------------------------------------------------------

        print("--- Maximum File Limitations")

        print("Attempt to freeze a folder with more than max allowed files")
        data["pathname"] = "/testdata/MaxFiles"
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Maximum allowed file count for a single action was exceeded.")

        # TODO: Verify after failed freeze request that files are still in staging and no pending action exists

        print("Freeze a folder with max allowed files")
        data["pathname"] = "/testdata/MaxFiles/%s_files" % (self.config["MAX_FILE_COUNT"])
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Freeze one additional file to folder with max allowed files")
        data["pathname"] = "/testdata/MaxFiles/test_file.dat"
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        action_data = response.json()
        action_pid = action_data["pid"]
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Attempt to unfreeze a frozen folder with more than max allowed files")
        data["pathname"] = "/testdata/MaxFiles"
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Maximum allowed file count for a single action was exceeded.")

        print("Attempt to delete a frozen folder with more than max allowed files")
        data["pathname"] = "/testdata/MaxFiles"
        response = requests.post("%s/delete" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Maximum allowed file count for a single action was exceeded.")

        print("Unfreeze a folder with max allowed files")
        data["pathname"] = "/testdata/MaxFiles/%s_files" % (self.config["MAX_FILE_COUNT"])
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200, response.text)

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Freeze a folder with max allowed files")
        data["pathname"] = "/testdata/MaxFiles/%s_files" % (self.config["MAX_FILE_COUNT"])
        response = requests.post("%s/freeze" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Delete a folder with max allowed files")
        data["pathname"] = "/testdata/MaxFiles/%s_files" % (self.config["MAX_FILE_COUNT"])
        response = requests.post("%s/delete" % self.config["IDA_API"], headers=headers, json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        # --------------------------------------------------------------------------------

        print("--- Action Record Operations")

        print("Retrieve set of suspend actions")
        data = {"status": "suspend"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)
        actions = response.json()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['project'], 'test_project_s')
        self.assertEqual(actions[0]['action'], 'suspend')

        print("Retrieve set of completed actions")
        data = {"projects": "test_project_a", "status": "completed"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 13)
        action_data = action_set_data[0]
        action_pid = action_data["pid"]
        self.assertIsNotNone(action_data.get("completed"))

        print("Update action as pending, clearing completed timestamp")
        data = {"completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNone(action_data.get("completed"))

        print("Retrieve set of pending actions")
        data = {"projects": "test_project_a", "status": "pending"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 1)
        action_data = action_set_data[0]
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNone(action_data.get("completed"))

        print("Update action as incomplete, clearing storage timestamp")
        data = {"storage": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNone(action_data.get("storage"))
        self.assertIsNone(action_data.get("completed"))

        print("Retrieve set of incomplete actions")
        data = {"projects": "test_project_a", "status": "incomplete"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 1)
        action_data = action_set_data[0]
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNone(action_data.get("storage"))
        self.assertIsNone(action_data.get("completed"))

        print("Update action as failed with error message")
        data = {"error": "test error message", "failed": "2099-01-01T00:00:00Z", "completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], action_pid)
        self.assertEqual(action_data["error"], data["error"])
        self.assertEqual(action_data["failed"], data["failed"])
        self.assertIsNone(action_data.get("storage"))
        self.assertIsNone(action_data.get("completed"))

        print("Retrieve set of failed actions")
        data = {"projects": "test_project_a", "status": "failed"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 1)
        action_data = action_set_data[0]
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNotNone(action_data.get("error"))
        self.assertIsNotNone(action_data.get("failed"))
        self.assertIsNone(action_data.get("storage"))
        self.assertIsNone(action_data.get("completed"))

        print("Clear failed action")
        response = requests.post("%s/clear/%s" % (self.config["IDA_API"], action_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNotNone(action_data.get("cleared"))

        print("Attempt to retrieve set of actions for project user has no rights to")
        data = {"projects": "test_project_c"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 0)

        # --------------------------------------------------------------------------------

        print("--- File Record Operations")

        print("Freeze a single file")
        data = {"project": "test_project_a", "pathname": "/testdata/License.txt"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Retrieve frozen file details by pathname")
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        file_pid = file_data["pid"]
        file_node = file_data["node"]

        print("Retrieve frozen file details by PID")
        response = requests.get("%s/files/%s" % (self.config["IDA_API"], file_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data_2 = response.json()
        self.assertEqual(file_data_2["id"], file_data["id"])

        print("Retrieve frozen file details by Nextcloud node ID")
        response = requests.get("%s/files/byNextcloudNodeId/%d" % (self.config["IDA_API"], file_node), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data_2 = response.json()
        self.assertEqual(file_data_2["id"], file_data["id"])

        print("Attempt to retrieve details of file user has no rights to")
        response = requests.get("%s/files/%s" % (self.config["IDA_API"], file_pid), auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Update checksum as plain checksum value")
        data = {"checksum": "thisisaplainchecksumvalue"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pid"], file_pid)
        self.assertEqual(file_data["checksum"], "sha256:thisisaplainchecksumvalue")

        print("Update checksum as sha256: checksum URI")
        data = {"checksum": "sha256:thisisachecksumuri"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pid"], file_pid)
        self.assertEqual(file_data["checksum"], "sha256:thisisachecksumuri")

        print("Update size")
        data = {"size": 1234}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pid"], file_pid)
        self.assertEqual(file_data["size"], data["size"])

        print("Update metadata timestamp")
        data = {"metadata": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pid"], file_pid)
        self.assertEqual(file_data["metadata"], data["metadata"])

        print("Clear removed timestamp")
        data = {"removed": "null"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pid"], file_pid)
        self.assertIsNone(file_data.get("removed"))

        print("Set removed timestamp")
        data = {"removed": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        file_data = response.json()
        self.assertEqual(file_data["pid"], file_pid)
        self.assertEqual(file_data["removed"], data["removed"])

        print("Attempt to retrieve removed file details by pathname")
        data = {"project": "test_project_a", "pathname": "/testdata/License.txt"}
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Attempt to retrieve removed file details by PID")
        response = requests.get("%s/files/%s" % (self.config["IDA_API"], file_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Attempt to retrieve removed file details by Nextcloud node ID")
        response = requests.get("%s/files/byNextcloudNodeId/%d" % (self.config["IDA_API"], file_node), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 404)

        # --------------------------------------------------------------------------------

        print("--- Invalid Timestamps")

        # All of the preceding tests cover expected behavior with valid timestamps used. The
        # following tests ensure that requests with invalid timestamps are rejected.

        print("Attempt to set invalid timestamp: date only, no time")
        data = {"removed": "2017-11-12"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Specified timestamp \"2017-11-12\" is invalid")

        print("Attempt to set invalid timestamp: invalid time separator syntax")
        data = {"removed": "2017-11-12 15:48:15Z"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Specified timestamp \"2017-11-12 15:48:15Z\" is invalid")

        print("Attempt to set invalid timestamp: invalid timezone")
        data = {"removed": "2017-11-12T15:48:15+0000"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Specified timestamp \"2017-11-12T15:48:15+0000\" is invalid")

        print("Attempt to set invalid timestamp: invalid format")
        data = {"removed": "Tue, Dec 12, 2017 10:03 UTC"}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Specified timestamp \"Tue, Dec 12, 2017 10:03 UTC\" is invalid")

        # --------------------------------------------------------------------------------

        print("--- Failed Actions")

        # Strategy: freeze a file, waiting for action to complete. Clear all postprocessing
        # related timestamps, i.e. all following the Pids timestamp, and mark the action as
        # failed. Then retry the failed freeze action, which will result in all postprocesing
        # steps being redone (even though unnecesary)

        print("Freeze a single file")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/baseline/test02.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        action_pid = action_data["pid"]
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Update action as failed, clearing postprocessing timestamps")
        data = {
            "error":       "test error message",
            "failed":      "2099-01-01T00:00:00Z",
            "checksums":   "null",
            "metadata":    "null",
            "replication": "null",
            "completed":   "null"
        }
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], action_pid)
        self.assertEqual(action_data["error"], data["error"])
        self.assertEqual(action_data["failed"], data["failed"])
        self.assertIsNone(action_data.get("checksums"))
        self.assertIsNone(action_data.get("metadata"))
        self.assertIsNone(action_data.get("replication"))
        self.assertIsNone(action_data.get("completed"))

        print("Retrieve set of failed actions")
        data = {"projects": "test_project_a", "status": "failed"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 1)
        action_data = action_set_data[0]
        self.assertEqual(action_data["pid"], action_pid)
        self.assertIsNotNone(action_data.get("error"))
        self.assertIsNotNone(action_data.get("failed"))
        self.assertIsNone(action_data.get("checksums"))
        self.assertIsNone(action_data.get("metadata"))
        self.assertIsNone(action_data.get("replication"))
        self.assertIsNone(action_data.get("completed"))
        self.assertIsNone(action_data.get("retry"))
        self.assertIsNone(action_data.get("retrying"))

        print("Retry failed action")
        response = requests.post("%s/retry/%s" % (self.config["IDA_API"], action_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertIsNotNone(action_data["pid"])
        self.assertEqual(action_data.get("retrying"), action_pid)
        self.assertIsNone(action_data.get("retry"))
        self.assertIsNone(action_data.get("cleared"))
        self.assertIsNone(action_data.get("error"))
        self.assertIsNone(action_data.get("failed"))
        retry_action_pid = action_data["pid"]

        print("Retrieve updated failed action")
        response = requests.get("%s/actions/%s" % (self.config["IDA_API"], action_pid), auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], action_pid)
        self.assertEqual(action_data.get("retry"), retry_action_pid)
        self.assertIsNone(action_data.get("retrying"))
        self.assertIsNotNone(action_data.get("failed"))
        self.assertIsNotNone(action_data.get("cleared"))

        wait_for_pending_actions(self, "test_project_a", test_user_a)
        check_for_failed_actions(self, "test_project_a", test_user_a)

        print("Verify set of failed actions is empty")
        data = {"project": "test_project_a", "status": "failed"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 0)

        print("Update retry action as failed")
        data = {"error": "test error message", "failed": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], retry_action_pid), json=data, auth=pso_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["pid"], retry_action_pid)
        self.assertEqual(action_data["error"], data["error"])
        self.assertEqual(action_data["failed"], data["failed"])

        print("Retrieve set of failed actions")
        data = {"projects": "test_project_a", "status": "failed"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 1)
        action_data = action_set_data[0]
        self.assertEqual(action_data["pid"], retry_action_pid)

        print("Clear all failed actions for project")
        data = {"projects": "test_project_a", "status": "failed"}
        response = requests.post("%s/clearall" % (self.config["IDA_API"]), json=data, auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify set of failed actions is empty")
        data = {"project": "test_project_a", "status": "failed"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 0)

        # --------------------------------------------------------------------------------

        print("--- Access Control")

        # All of the preceding tests cover expected behavior with the credentials used. The
        # following tests ensure that requests with inappropriate credentials are rejected.

        print("Attempt to freeze file as admin user")
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_2/test01.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to retrieve file details from project to which user does not belong")
        data = {"project": "test_project_a", "pathname": "/testdata/2017-08/Experiment_1/test05.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to freeze file in project to which user does not belong")
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test05.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to update action as pending, clearing completed timestamp, as normal user")
        data = {"completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_pid), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to update file size as normal user")
        data = {"size": 1234}
        response = requests.post("%s/files/%s" % (self.config["IDA_API"], file_pid), json=data, auth=test_user_a, verify=False)
        self.assertEqual(response.status_code, 403)

        # --------------------------------------------------------------------------------

        print("--- Project Locking")

        print("Verify that project is unlocked")
        # GET /app/ida/api/lock/test_project_c as test_user_c should fail with 404 Not found
        response = requests.get("%s/lock/test_project_c" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Attempt to lock project as regular user")
        # POST /app/ida/api/lock/test_project_c as test_user_c should fail with 403 Unauthorized
        response = requests.post("%s/lock/test_project_c" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Lock project")
        # POST /app/ida/api/lock/test_project_c as pso_user_c should succeed with 200 OK
        response = requests.post("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that project is locked")
        # GET /app/ida/api/lock/test_project_c as test_user_c should succeed with 200 OK
        response = requests.get("%s/lock/test_project_c" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Attempt to lock already locked project")
        # POST /app/ida/api/lock/test_project_c as pso_user_c should fail with 409 Conflict due
        # to already locked project
        response = requests.post("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Unable to lock the specified project.", response.text)

        print("Attempt to freeze file while project is locked")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test01.dat
        # should fail with 409 Conflict due to locked project
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test01.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Failed to lock project when initiating requested action.", response.text)

        print("Attempt to unlock project as regular user")
        # DELETE /app/ida/api/lock/test_project_c as test_user_c should fail with 403 Unauthorized
        response = requests.delete("%s/lock/test_project_c" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Unlock project")
        # DELETE /app/ida/api/lock/test_project_c as pso_user_c should succeed with 200 OK
        response = requests.delete("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that project is unlocked")
        # GET /app/ida/api/lock/test_project_c as test_user_c should fail with 404 Not found
        response = requests.get("%s/lock/test_project_c" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Unlock already unlocked project")
        # DELETE /app/ida/api/lock/test_project_c as pso_user_c should still succeed with 200 OK
        response = requests.delete("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Freeze a file in an unlocked project")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test01.dat
        # should succeed with 200 OK as project is not locked
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # --------------------------------------------------------------------------------

        print("--- Service Locking")

        print("Verify that service is unlocked")
        # GET /app/ida/api/lock/all as test_user_c should fail with 404 Not found
        response = requests.get("%s/lock/all" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Attempt to lock service as regular user")
        # POST /app/ida/api/lock/all as test_user_c should fail with 403 Unauthorized
        response = requests.post("%s/lock/all" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to lock service as project share owner")
        # POST /app/ida/api/lock/all as pso_user_c should fail with 403 Unauthorized
        response = requests.post("%s/lock/all" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Lock service")
        # POST /app/ida/api/lock/all as admin_user should succeed with 200 OK
        response = requests.post("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that service is locked as regular user")
        # GET /app/ida/api/lock/all as test_user_c should succeed with 200 OK
        response = requests.get("%s/lock/all" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that service is locked as project share owner")
        # GET /app/ida/api/lock/all as pso_user_c should succeed with 200 OK
        response = requests.get("%s/lock/all" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that service is locked as admin user")
        # GET /app/ida/api/lock/all as admin_user should succeed with 200 OK
        response = requests.get("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Attempt to lock project while service is locked")
        # POST /app/ida/api/lock/test_project_c as pso_user_c should fail with 409 Conflict as
        # can't lock a project when service is locked
        response = requests.post("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Unable to lock the specified project.", response.text)

        print("Lock already locked service")
        # POST /app/ida/api/lock/all as admin_user should still succeed with 200 OK
        response = requests.post("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Attempt to freeze file while service is locked")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test02.dat
        # should fail with 409 Conflict due to locked project
        data["pathname"] = "/testdata/2017-08/Experiment_1/test02.dat"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Failed to lock project when initiating requested action.", response.text)

        print("Verify all scope checks fail while service is locked")
        # All of the following requests as test_user_c should fail with 409 Conflict as service is locked:
        data["pathname"] = "/"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)
        data["pathname"] = "/testdata"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)
        data["pathname"] = "/testdata/2017-08"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)
        data["pathname"] = "/testdata/2017-08/Experiment_1"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)
        data["pathname"] = "/testdata/2017-08/Experiment_1/test01.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)
        data["pathname"] = "/testdata/2017-08/Contact.txt"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)
        data["pathname"] = "/X/Y/Z"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('The specified scope conflicts with an ongoing action in the specified project.', response.text)

        print("Attempt to unlock service as regular user")
        # DELETE /app/ida/api/lock/all as test_user_c should fail with 403 Unauthorized
        response = requests.delete("%s/lock/all" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Attempt to unlock service as project share owner")
        # DELETE /app/ida/api/lock/all as PSO_test_project_c should fail with 403 Unauthorized
        response = requests.delete("%s/lock/all" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 403)

        print("Unlock service")
        # DELETE /app/ida/api/lock/all as admin_user should succeed with 200 OK
        response = requests.delete("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that service is unlocked")
        # GET /app/ida/api/lock/all as test_user_c should fail with 404 Not found
        response = requests.get("%s/lock/all" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Unlock already unlocked service")
        # DELETE /app/ida/api/lock/all as admin_user should still succeed with 200 OK
        response = requests.delete("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Freeze file in unlocked service")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test02.dat as
        # test_user_c should succeed with 200 OK as service is not locked
        data["pathname"] = "/testdata/2017-08/Experiment_1/test02.dat"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json() # For use in subsequent action collision tests below

        wait_for_pending_actions(self, "test_project_c", test_user_c)
        check_for_failed_actions(self, "test_project_c", test_user_c)

        print("Lock project in unlocked service")
        # POST /app/ida/api/lock/test_project_c as pso_user_c should succeed with 200 OK
        response = requests.post("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Lock service even though project is locked")
        # POST /app/ida/api/lock/all as admin_user should succeed with 200 OK
        response = requests.post("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Unlock project even though service is locked")
        # DELETE /app/ida/api/lock/test_project_c as pso_user_c should succeed with 200 OK as it
        # should be allowed to unlock a project even when the service is locked
        response = requests.delete("%s/lock/test_project_c" % self.config["IDA_API"], auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Unlock service")
        # DELETE /app/ida/api/lock/all as admin_user should succeed with 200 OK
        response = requests.delete("%s/lock/all" % self.config["IDA_API"], auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        # --------------------------------------------------------------------------------

        print("--- Action Collisions")

        print("Simulate pending action")
        # Simulate pending freeze action by removing completed timestamp from preceeding action
        # (frozen pending action pathname = "/testdata/2017-08/Experiment_1/test02.dat")
        data = {"completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Create new file in staging with same pathname as file in scope of pending action")
        # pathname = "/testdata/2017-08/Experiment_1/test02.dat"
        cmd = "touch %s/PSO_test_project_c/files/test_project_c+/testdata/2017-08/Experiment_1/test02.dat" % (self.config["STORAGE_OC_DATA_ROOT"])
        os.system(cmd)
        cmd = "sudo -u %s %s/nextcloud/occ files:scan PSO_test_project_c 2>&1 >/dev/null" % (self.config["HTTPD_USER"], self.config["ROOT"])
        os.system(cmd)

        print("Attempt to freeze folder which intersects with file associated with pending action")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1 as test_user_c
        # should fail with 409 Conflict due to collision with the previous pending action
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("The requested action conflicts with an ongoing action in the specified project.", response.text)

        print("Freeze file which does not intersect with pending action")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-10/Experiment_3/test01.dat
        # should succeed with 200 OK
        data["pathname"] = "/testdata/2017-10/Experiment_3/test01.dat"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify that project is unlocked")
        # GET /app/ida/api/lock/test_project_c as test_user_c should fail with 404 Not found
        response = requests.get("%s/lock/test_project_c" % self.config["IDA_API"], auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 404)

        print("Complete simulated pending action")
        # Update simulated action to be fully completed with all timestamps defined
        data = {"completed": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_c", test_user_c)
        check_for_failed_actions(self, "test_project_c", test_user_c)

        print("Attempt to freeze folder which intersects with file already in frozen area")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1 as test_user_c
        # should fail with 409 Conflict due to collision with existing file in frozen area
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("The requested action conflicts with an existing file in the frozen area.", response.text)

        print("Remove new file in staging with same pathname as file in scope of pending action")
        # pathname = "/testdata/2017-08/Experiment_1/test02.dat"
        cmd = "rm %s/PSO_test_project_c/files/test_project_c+/testdata/2017-08/Experiment_1/test02.dat" % (self.config["STORAGE_OC_DATA_ROOT"])
        os.system(cmd)
        cmd = "sudo -u %s %s/nextcloud/occ files:scan PSO_test_project_c 2>&1 >/dev/null" % (self.config["HTTPD_USER"], self.config["ROOT"])
        os.system(cmd)

        print("Freeze folder which no longer intersects with pending action or existing file in frozen area")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1 as
        # test_user_c should succeed with 200 OK
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json() # For use in subsequent action collision tests below

        wait_for_pending_actions(self, "test_project_c", test_user_c)
        check_for_failed_actions(self, "test_project_c", test_user_c)

        print("Simulate pending freeze action")
        # Simulate pending freeze action by removing completed timestamp from preceeding action
        # (frozen pending action pathname = "/testdata/2017-08/Experiment_1")
        data = {"completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Attempt to delete frozen file which intersects with file associated with pending action")
        # POST /app/ida/api/delete?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test04.dat as test_user_c
        # should fail with 409 Conflict due to collision with the previous pending action
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test04.dat"}
        response = requests.post("%s/delete" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("The requested action conflicts with an ongoing action in the specified project.", response.text)

        print("Attempt to unfreeze frozen file which intersects with file associated with pending freeze action")
        # POST /app/ida/api/unfreeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test03.dat as test_user_c
        # should fail with 409 Conflict due to collision with the previous pending action
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test03.dat"}
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("The requested action conflicts with an ongoing action in the specified project.", response.text)

        print("Complete simulated pending freeze action")
        # Update simulated action to be fully completed with all timestamps defined
        data = {"completed": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Delete frozen file which no longer intersects with file associated with pending action")
        # POST /app/ida/api/delete?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test04.dat as test_user_c
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test04.dat"}
        response = requests.post("%s/delete" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Unfreeze frozen file which no longer intersects with file associated with pending action")
        # POST /app/ida/api/unfreeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test03.dat as test_user_c
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test03.dat"}
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json() # For use in subsequent action collision tests below

        wait_for_pending_actions(self, "test_project_c", test_user_c)
        check_for_failed_actions(self, "test_project_c", test_user_c)

        print("Simulate pending unfreeze action")
        # Simulate pending unfreeze action by removing completed timestamp from preceeding action
        # (unfrozen pending action pathname = "/testdata/2017-08/Experiment_1/test03.dat")
        data = {"completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Attempt to freeze file which intersects with file associated with pending unfreeze action")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test03.dat as test_user_c
        # should fail with 409 Conflict due to collision with the previous pending action
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test03.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn("The requested action conflicts with an ongoing action in the specified project.", response.text)

        print("Complete simulated pending unfreeze action")
        # Update simulated action to be fully completed with all timestamps defined
        data = {"completed": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Freeze frozen file which no longer intersects with file associated with pending action")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-08/Experiment_1/test03.dat as test_user_c
        data = {"project": "test_project_c", "pathname": "/testdata/2017-08/Experiment_1/test03.dat"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        wait_for_pending_actions(self, "test_project_c", test_user_c)
        check_for_failed_actions(self, "test_project_c", test_user_c)

        # --------------------------------------------------------------------------------

        print("--- Scope Collisions")

        print("Freeze folder which does not intersect with pending action or existing file in frozen area")
        # POST /app/ida/api/freeze?project=test_project_c&pathname=/testdata/2017-11/Experiment_6 should succeed with 200 OK
        data = {"project": "test_project_c", "pathname": "/testdata/2017-11/Experiment_6"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json() # For use in subsequent action collision tests below

        wait_for_pending_actions(self, "test_project_c", test_user_c)
        check_for_failed_actions(self, "test_project_c", test_user_c)

        print("Simulate initiating action")
        # Simulate initiating freeze action by removing all step timestamps from preceeding action following pids timestamp
        # (frozen pending action pathname = "/testdata/2017-11/Experiment_6")
        data = {"storage": "null", "checksums": "null", "metadata": "null", "replication": "null", "completed": "null"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify disallowed scopes are rejected")
        # All of the following as test_user_c should fail with 409 Conflict:
        data = {"project": "test_project_c"}

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/
        data["pathname"] = "/"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata
        data["pathname"] = "/testdata"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11
        data["pathname"] = "/testdata/2017-11"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6
        data["pathname"] = "/testdata/2017-11/Experiment_6"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6/test9999.dat
        data["pathname"] = "/testdata/2017-11/Experiment_6/test9999.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6/baseline/testXYZ.dat
        data["pathname"] = "/testdata/2017-11/Experiment_6/baseline/testXYZ.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6/.hidden_file.dat
        data["pathname"] = "/testdata/2017-11/Experiment_6/.hidden_file.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        print("Verify allowed scopes are OK")
        # All of the following as test_user_c should succeed with 200 OK:

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/XYZ
        data["pathname"] = "/XYZ"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2018-08
        data["pathname"] = "/testdata/2018-08"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2018-08/test05.dat
        data["pathname"] = "/testdata/2018-08/test05.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-10/Experiment_5
        data["pathname"] = "/testdata/2017-10/Experiment_5"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/Contact.txt
        data["pathname"] = "/Contact.txt"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-10/Experiment_2/baseline/test03.dat
        data["pathname"] = "/testdata/2017-10/Experiment_2/baseline/test03.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        print("Verify root scope blocks all other scopes")

        # Record incomplete freeze action as completed
        data = {"completed": "2099-01-01T00:00:00Z"}
        response = requests.post("%s/actions/%s" % (self.config["IDA_API"], action_data["pid"]), json=data, auth=pso_user_c, verify=False)
        self.assertEqual(response.status_code, 200)

        # Verify no incomplete actions
        data = {"project": "test_project_c", "status": "incomplete"}
        response = requests.get("%s/actions" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 200)
        action_set_data = response.json()
        self.assertEqual(len(action_set_data), 0)

        # Simulate repair action with scope "/" and ensure every possible other scope is blocked
        data = {"action": "repair", "project": "test_project_c", "pathname": "/"}
        response = requests.post("%s/actions" % self.config["IDA_API"], json=data, auth=admin_user, verify=False)
        self.assertEqual(response.status_code, 200)

        # All of the following as test_user_c should fail with 409 Conflict:
        data = {"project": "test_project_c"}

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/
        data["pathname"] = "/"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata
        data["pathname"] = "/testdata"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11
        data["pathname"] = "/testdata/2017-11"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6
        data["pathname"] = "/testdata/2017-11/Experiment_6"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6/test9999.dat
        data["pathname"] = "/testdata/2017-11/Experiment_6/test9999.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6/baseline/testXYZ.dat
        data["pathname"] = "/testdata/2017-11/Experiment_6/baseline/testXYZ.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-11/Experiment_6/.hidden_file.dat
        data["pathname"] = "/testdata/2017-11/Experiment_6/.hidden_file.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/XYZ
        data["pathname"] = "/XYZ"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/2018-08
        data["pathname"] = "/testdata/2017-08"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/2018-08/test05.dat
        data["pathname"] = "/testdata/2017-08/test05.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-10/Experiment_5
        data["pathname"] = "/testdata/2017-10/Experiment_5"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/Contact.txt
        data["pathname"] = "/Contact.txt"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # POST /app/ida/api/scopeOK?project=test_project_c&pathname=/testdata/2017-10/Experiment_2/baseline/test03.dat
        data["pathname"] = "/testdata/2017-10/Experiment_2/baseline/test03.dat"
        response = requests.post("%s/scopeOK" % self.config["IDA_API"], json=data, auth=test_user_c, verify=False)
        self.assertEqual(response.status_code, 409)

        # --------------------------------------------------------------------------------

        print("--- Repair Actions (IDA API only)")

        # NOTE: More comprehensive testing of the repair functionality is provided by the
        # tests for auditing, such that after the various invalid project conditions are
        # manually created prior to the auditing tests, the invalid projects are all repaired
        # and re-audited to verify that no further errors are reported.

        print("Freeze a folder")
        data = {"project": "test_project_d", "pathname": "/testdata/2017-08/Experiment_1"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        action_pid = action_data["pid"]
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_d", test_user_d)
        check_for_failed_actions(self, "test_project_d", test_user_d)

        print("Retrieve details of all frozen files associated with freeze action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        # File count for this freeze folder action should always be the same, based on the static test data initialized
        self.assertEqual(len(file_set_data), 13)
        file_data = file_set_data[0]
        self.assertIsNotNone(file_data.get("frozen"))
        self.assertIsNone(file_data.get("cleared"))
        # Save key values for later checks
        original_action_pid = action_data["pid"]
        original_action_file_count = 13
        original_first_file_record_id = file_data["id"]
        original_first_file_pid = file_data["pid"]
        original_first_file_pathname = file_data["pathname"]

        print("Retrieve file details from hidden frozen file")
        data = {"project": "test_project_d", "pathname": "/testdata/2017-08/Experiment_1/.hidden_file"}
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        file_x_data = response.json()
        self.assertEqual(file_x_data.get('size'), 446)

        print("Repair project...")
        response = requests.post("%s/repair" % self.config["IDA_API"], auth=pso_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        action_pid = action_data["pid"]
        self.assertEqual(action_data["action"], "repair")
        self.assertEqual(action_data["pathname"], "/")

        wait_for_pending_actions(self, "test_project_d", test_user_d)
        check_for_failed_actions(self, "test_project_d", test_user_d)

        print("Retrieve details of all frozen files associated with repair action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], action_data["pid"]), auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        # Total count of frozen files should remain the same
        self.assertEqual(len(file_set_data), original_action_file_count)
        file_data = file_set_data[0]
        # First frozen file record should be clone of original and have different record id
        self.assertNotEqual(file_data["id"], original_first_file_record_id)
        # PID and pathname should not have changed for cloned file record
        self.assertEqual(file_data["pid"], original_first_file_pid)
        self.assertEqual(file_data["pathname"], original_first_file_pathname)
        # New cloned file record should be frozen but not cleared
        self.assertIsNotNone(file_data.get("frozen"))
        self.assertIsNone(file_data.get("cleared"))

        print("Retrieve details of all frozen files associated with original freeze action")
        response = requests.get("%s/files/action/%s" % (self.config["IDA_API"], original_action_pid), auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        file_set_data = response.json()
        self.assertEqual(len(file_set_data), original_action_file_count)
        file_data = file_set_data[0]
        self.assertEqual(file_data["id"], original_first_file_record_id)
        # Original frozen file record should be both frozen and also now cleared
        self.assertIsNotNone(file_data.get("frozen"))
        self.assertIsNotNone(file_data.get("cleared"))

        print("Retrieve file details from hidden frozen file")
        data = {"project": "test_project_d", "pathname": "/testdata/2017-08/Experiment_1/.hidden_file"}
        response = requests.get("%s/files/byProjectPathname/%s" % (self.config["IDA_API"], data["project"]), json=data, auth=test_user_d, verify=False)
        self.assertEqual(response.status_code, 200)
        file_x_data = response.json()
        self.assertEqual(file_x_data.get('size'), 446)

        # NOTE tests for postprocessing results of repair action are handled in /tests/agents/test_agents.py

        # --------------------------------------------------------------------------------

        print("--- Batch Actions")

        frozen_area_root = "%s/PSO_test_project_b/files/test_project_b" % (self.config["STORAGE_OC_DATA_ROOT"])
        staging_area_root = "%s/PSO_test_project_b/files/test_project_b%s" % (self.config["STORAGE_OC_DATA_ROOT"], self.config["STAGING_FOLDER_SUFFIX"])
        cmd_base="sudo -u %s SIMULATE_AGENTS=true DEBUG=false %s/utils/admin/execute-batch-action" % (self.config["HTTPD_USER"], self.config["ROOT"])

        print("Attempt to freeze a folder with more than max allowed files")
        data = {"project": "test_project_b", "pathname": "/testdata/MaxFiles"}
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['message'], "Maximum allowed file count for a single action was exceeded.")

        print("Batch freeze a folder with more than max allowed files")
        cmd = "%s test_project_b freeze /testdata/MaxFiles >/dev/null" % (cmd_base)
        result = os.system(cmd)
        self.assertEqual(result, 0)

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify data was physically moved from staging to frozen area")
        self.assertFalse(os.path.exists("%s/testdata/MaxFiles/%s_files/500_files_1/100_files_1/10_files_1/test_file_1.dat" % (staging_area_root, self.config["MAX_FILE_COUNT"])))
        self.assertFalse(os.path.exists("%s/testdata/MaxFiles" % (staging_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/MaxFiles/%s_files/500_files_1/100_files_1/10_files_1/test_file_1.dat" % (frozen_area_root, self.config["MAX_FILE_COUNT"])))

        print("Batch unfreeze a folder with more than max allowed files")
        cmd = "%s test_project_b unfreeze /testdata/MaxFiles >/dev/null" % (cmd_base)
        result = os.system(cmd)
        self.assertEqual(result, 0)

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify data was physically moved from frozen to staging area")
        self.assertFalse(os.path.exists("%s/testdata/MaxFiles/%s_files/500_files_1/100_files_1/10_files_1/test_file_1.dat" % (frozen_area_root, self.config["MAX_FILE_COUNT"])))
        self.assertFalse(os.path.exists("%s/testdata/MaxFiles" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/MaxFiles/%s_files/500_files_1/100_files_1/10_files_1/test_file_1.dat" % (staging_area_root, self.config["MAX_FILE_COUNT"])))

        print("Batch freeze a folder with more than max allowed files")
        cmd = "%s test_project_b freeze /testdata/MaxFiles >/dev/null" % (cmd_base)
        result = os.system(cmd)
        self.assertEqual(result, 0)

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Batch delete a folder with more than max allowed files")
        cmd = "%s test_project_b delete /testdata/MaxFiles >/dev/null" % (cmd_base)
        result = os.system(cmd)
        self.assertEqual(result, 0)

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify data was physically removed from frozen area")
        self.assertFalse(os.path.exists("%s/testdata/MaxFiles" % (frozen_area_root)))

        # --------------------------------------------------------------------------------

        print("--- Root Folder Actions")

        frozen_area_root = "%s/PSO_test_project_b/files/test_project_b" % (self.config["STORAGE_OC_DATA_ROOT"])
        staging_area_root = "%s/PSO_test_project_b/files/test_project_b%s" % (self.config["STORAGE_OC_DATA_ROOT"], self.config["STAGING_FOLDER_SUFFIX"])

        data = {"project": "test_project_b"}

        print("Freeze a folder")
        data["pathname"] = "/testdata/2017-08/Experiment_1"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify data was physically moved from staging to frozen area")
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (frozen_area_root)))
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (staging_area_root)))

        print("Unfreeze all files in frozen area")
        data["pathname"] = "/"
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "unfreeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify all data was physically moved from frozen to staging area")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (frozen_area_root)))
        self.assertFalse(os.path.exists("%s/testdata" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (staging_area_root)))

        print("Freeze a folder")
        data["pathname"] = "/testdata/2017-08/Experiment_2"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify data was physically moved from staging to frozen area")
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline/test01.dat" % (frozen_area_root)))
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline/test01.dat" % (staging_area_root)))

        print("Unfreeze file in frozen area")
        data["pathname"] = "/testdata/2017-08/Experiment_2/baseline/test01.dat"
        response = requests.post("%s/unfreeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "unfreeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify file was physically moved from frozen to staging area")
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline/test01.dat" % (staging_area_root)))

        print("Freeze parent folder of unfrozen file")
        data["pathname"] = "/testdata/2017-08/Experiment_2/baseline"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify data was physically moved from staging to frozen area")
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline/test01.dat" % (frozen_area_root)))
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline/test01.dat" % (staging_area_root)))
        self.assertFalse(os.path.exists("%s/testdata/2017-08/Experiment_2/baseline" % (staging_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_2" % (staging_area_root)))

        print("Freeze all files in staging area")
        data["pathname"] = "/"
        response = requests.post("%s/freeze" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "freeze")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify all data was physically moved from staging to frozen area")
        self.assertTrue(os.path.exists("%s/testdata" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_1/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-08/Experiment_2/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-10/Experiment_3/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-10/Experiment_4/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-10/Experiment_5/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-11/Experiment_6/test01.dat" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/2017-11/Experiment_7/baseline/.hidden_file" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/Contact.txt" % (frozen_area_root)))
        self.assertTrue(os.path.exists("%s/testdata/License.txt" % (frozen_area_root)))
        self.assertFalse(os.path.exists("%s/testdata" % (staging_area_root)))

        print("Delete all files in frozen area")
        response = requests.post("%s/delete" % self.config["IDA_API"], json=data, auth=test_user_b, verify=False)
        self.assertEqual(response.status_code, 200)
        action_data = response.json()
        self.assertEqual(action_data["action"], "delete")
        self.assertEqual(action_data["project"], data["project"])
        self.assertEqual(action_data["pathname"], data["pathname"])

        wait_for_pending_actions(self, "test_project_b", test_user_b)
        check_for_failed_actions(self, "test_project_b", test_user_b)

        print("Verify all data was physically removed from frozen area")
        self.assertFalse(os.path.exists("%s/testdata" % (frozen_area_root)))

        print("Verify both frozen and staging root folders still exist")
        self.assertTrue(os.path.exists(frozen_area_root))
        self.assertTrue(os.path.exists(staging_area_root))

        # --------------------------------------------------------------------------------
        # If all tests passed, record success, in which case tearDown will be done

        self.success = True

        # --------------------------------------------------------------------------------

        # TODO: consider which tests may be missing...

        # Possible additional tests:
        #    add tests for housekeeping operations as normal user, when must be admin or PSO user
        #    add tests for housekeeping operations as PSO user, when must be admin
        #    add tests attempting to copy files or folders to or within the frozen area (not fully covered by CLI tests)
        #    add tests for copying files or folders from the frozen area to the staging area (not fully covered by CLI tests)
        #    add tests for checking required parameters
        #    add tests for pathnames containing special characters

