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


import unittest
import subprocess
import os
from tests.common.utils import *


class TestIdaProject(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        print("=== tests/admin/test_ida_project")


    def setUp(self):
        self.config = load_configuration()
        self.project_name = "test_project_a"
        self.ida_project = "sudo -u %s DEBUG=false %s/admin/ida_project" % (self.config['HTTPD_USER'], self.config['ROOT'])
        self.ida_user = "sudo -u %s DEBUG=false %s/admin/ida_user" % (self.config['HTTPD_USER'], self.config['ROOT'])
        self.offlineSentinelFile = "%s/control/OFFLINE" % self.config.get('STORAGE_OC_DATA_ROOT', '/mnt/storage_vol01/ida')

        # clear any residual accounts, if they exist from a prior run
        self.success = True
        noflush = self.config.get('NO_FLUSH_AFTER_TESTS', 'false')
        self.config['NO_FLUSH_AFTER_TESTS'] = 'false'
        self.tearDown()
        self.success = False
        self.config['NO_FLUSH_AFTER_TESTS'] = noflush

        print("(initializing)")


    def tearDown(self):
        # clear all test accounts, ignoring any errors if they do not exist

        if self.success and self.config.get('NO_FLUSH_AFTER_TESTS', 'false') == 'false':

            print("(cleaning)")

            if (os.path.exists(self.offlineSentinelFile)) :
                os.remove(self.offlineSentinelFile)

            cmd = "sudo -u %s DEBUG=false %s/tests/utils/initialize-test-accounts --flush %s/tests/utils/single-project.config" % (self.config["HTTPD_USER"], self.config["ROOT"], self.config["ROOT"])
            os.system(cmd)

        self.assertTrue(self.success)


    def test_ida_project(self):

        print("Create new project")
        cmd = "%s ADD %s 1 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 0, "Project already exists")

        print("Attempt to create existing project")
        cmd = "%s ADD %s 1 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 1, "No existing project")

        print("Modify project quota")
        cmd = "%s MODIFY %s 2 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 0, "Cannot modify quota")

        print("Attempt to modify project quota with invalid non-number")
        cmd = "%s MODIFY %s 2e6 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 1, "Input is a valid number")

        print("Disable project")
        cmd = "%s DISABLE %s 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 0, "Cannot disable project")

        print("Attempt to disable non-existent project")
        cmd = "%s DISABLE %s 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 1, "User exists")

        print("Define project title")
        cmd = "%s TITLE %s \"Test title 123\" 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 0, "Setting project test_project title to \"Test title 123\"")
        titleFilePath = "%s/PSO_%s/files/TITLE" % (self.config["STORAGE_OC_DATA_ROOT"], self.project_name)
        self.assertTrue(os.path.exists(titleFilePath))
        self.assertEqual("Test title 123\n", open(titleFilePath).read())

        print("Change project title")
        cmd = "%s TITLE %s \"Test title 234\" 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 0, "Setting project test_project title to \"Test title 234\"")
        titleFilePath = "%s/PSO_%s/files/TITLE" % (self.config["STORAGE_OC_DATA_ROOT"], self.project_name)
        self.assertTrue(os.path.exists(titleFilePath))
        self.assertEqual("Test title 234\n", open(titleFilePath).read())

        self.assertTrue(make_ida_offline(self))

        print("Attempt to create new project while service in OFFLINE mode")
        cmd = "%s ADD %s 1 2>&1" % (self.ida_project, self.project_name)
        OUT = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        self.assertEqual(OUT, 1, "Sentinel file ignored")

        self.assertTrue(make_ida_online(self))

        self.success = True
