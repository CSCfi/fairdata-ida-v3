#--------------------------------------------------------------------------------
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
#--------------------------------------------------------------------------------

IDA_ENVIRONMENT="DEV"

DEBUG="false"
NO_FLUSH_AFTER_TESTS="false"
SEND_TEST_EMAILS="false"

ROOT="/var/ida"
OCC="/var/ida/nextcloud/occ"
LOG="/mnt/storage_vol01/log/ida.log"

HTTPD_USER="apache"

NC_ADMIN_USER="admin"
NC_ADMIN_PASS="DEFINE_ME"
PROJECT_USER_PASS="DEFINE_ME"
TEST_USER_PASS="DEFINE_ME"
BATCH_ACTION_TOKEN="DEFINE_ME"

DEMO_ACCT_MGMT_PASS="DEFINE_ME"

LDAP_HOST_URL="ldaps://DEFINE_ME"
LDAP_SEARCH_BASE="ou=idm,dc=csc,dc=fi"
LDAP_BIND_USER="uid=csc-data-deletion-read,ou=Custom,ou=Special Users,dc=csc,dc=fi"
LDAP_PASSWORD="****"

CSC_DATA_DELETION_MICROSERVICE="https://DEFINE_ME"
CSC_DATA_DELETION_SECURITY_TOKEN="DEFINE_ME"

DBTYPE="pgsql"
DBNAME="nextcloud30"
DBHOST="DEFINE_ME"
DBPORT=5432
DBTABLEPREFIX="oc_"
DBUSER="nextcloud"
DBPASSWORD="nextcloud"
DBROUSER="inspector"
DBROPASSWORD="DEFINE_ME"
DBADMUSER="admin"
DBADMPASSWORD="DEFINE_ME"

RABBIT_HOST="DEFINE_ME"
RABBIT_PORT=5672
RABBIT_WEB_API_PORT=15672
RABBIT_VHOST="ida-vhost"
RABBIT_ADMIN_USER="admin"
RABBIT_ADMIN_PASS="DEFINE_ME"
RABBIT_WORKER_USER="worker"
RABBIT_WORKER_PASS="DEFINE_ME"
RABBIT_WORKER_LOG_FILE="/mnt/storage_vol01/log/agents.log"
RABBIT_HEARTBEAT=0
RABBIT_MONITOR_USER="monitor"
RABBIT_MONITOR_PASS="DEFINE_ME"
RABBIT_MONITORING_DIR="/mnt/storage_vol01/log/rabbitmq_monitoring"

METAX_AVAILABLE=1
# v1
METAX_FILE_STORAGE_ID="urn:nbn:fi:att:file-storage-ida" # deprecated from Metax v3 onwards
METAX_USER="ida"                                        # deprecated from Metax v3 onwards
METAX_RPC="https://DEFINE_ME/rpc/v1"                    # deprecated from Metax v3 onwards
METAX_API="https://DEFINE_ME/rest/v1"
METAX_PASS="DEFINE_ME"
# v3
#METAX_API="https://DEFINE_ME/v3"
#METAX_PASS="DEFINE_ME"

PYTHON="/usr/local/fd/python3/bin/python"

IDA_API="https://LOCAL_SERVER_FQDN/apps/ida/api"
FILE_API="https://LOCAL_SERVER_FQDN/remote.php/webdav"
SHARE_API="https://LOCAL_SERVER_FQDN/ocs/v1.php/apps/files_sharing/api/v1/shares"
GROUP_API="https://LOCAL_SERVER_FQDN/ocs/v1.php/cloud/groups"
USER_API="https://LOCAL_SERVER_FQDN/ocs/v1.php/cloud/users"

IDA_CLI_ROOT="/var/ida-tools"

STORAGE_OC_DATA_ROOT="/mnt/storage_vol01/ida"
STORAGE_CANDIDATES=("/mnt/storage_vol01/ida" "/mnt/storage_vol02/ida" "/mnt/storage_vol03/ida" "/mnt/storage_vol04/ida")
DATA_REPLICATION_ROOT="/mnt/tape_archive_cache"
TRASH_DATA_ROOT="/mnt/storage_vol01/ida_trash"

QUARANTINE_PERIOD="7776000"   # 7776000 seconds = 90 days

EMAIL_SENDER="root@LOCAL_SERVER_FQDN"
EMAIL_RECIPIENTS="DEFINE_ME"  # Internal stakeholders

TEST_IDM_PROXY_USER_PASSWORD="DEFINE_ME"
TEST_IDM_CLIENT_PASSWORD="DEFINE_ME"
TEST_IDM_SHARED_SECRET="DEFINE_ME"

TEST_PAS_CONTRACT_ID="DEFINE_ME"

OLD_DATA_EXCLUDED_PROJECTS=""
