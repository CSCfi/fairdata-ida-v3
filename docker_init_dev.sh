#!/bin/bash
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
# Note: This script assumes that it is being executed at the root of the fairdata-ida
# repository and that the fairdata-docker repository is cloned as a sibling directory
# of the fairdata-ida repository, as specified in the instructions in Docker_Setup.md.
#--------------------------------------------------------------------------------

SCRIPT_ROOT=`dirname "$(realpath $0)"`

cd $SCRIPT_ROOT

if [ ! -e ../fairdata-docker/ida/config/config.dev.sh ]; then
    echo "Error: Could not find the IDA configuration file. Aborting." >&2
    exit 1
fi

. ../fairdata-docker/ida/config/config.dev.sh

if [ "$ROOT" = "" ]; then
    echo "Error: Failed to properly initialize script. Aborting." >&2
    exit 1
fi

HTTPD_USER="apache"

#--------------------------------------------------------------------------------
# Verify that we are in a test environment

if [ "$IDA_ENVIRONMENT" == "PRODUCTION" ]; then
    errorExit "Error: This script can not be run in a production environment. Aborting."
fi

#--------------------------------------------------------------------------------

# Open up permissions of the repository locally so the mounted volume is not overly restricted
chmod -R g+rwX,o+rX .

if [ -d ./config ];
then
    rm -fr ./config/*
else
    mkdir ./config 
fi

if [ -d ./nextcloud/config ];
then
    rm -fr ./nextcloud/config/*
else
    mkdir ./nextcloud/config 
fi

echo "Installing IDA config.sh..."
docker cp ../fairdata-docker/ida/config/config.dev.sh $(docker ps -q -f name=ida-nextcloud):/var/ida/config/config.sh
docker exec -it $(docker ps -q -f name=ida-nextcloud) chown -R $HTTPD_USER:$HTTPD_USER /var/ida/config

echo "Installing IDA healthcheck sevice config.json..."
docker cp ../fairdata-docker/ida/healthcheck/config.json $(docker ps -q -f name=ida-nextcloud):/usr/local/fd/fairdata-ida-healthcheck/config.json
docker exec -it $(docker ps -q -f name=ida-nextcloud) chown -R root:root /usr/local/fd/fairdata-ida-healthcheck/config.json

echo "Installing Download service settings.cfg..."
docker cp ../fairdata-docker/download/config/download-settings.idadev.cfg $(docker ps -q -f name=ida-nextcloud):/usr/local/fd/fairdata-download/dev_config/settings.cfg
docker exec -it $(docker ps -q -f name=ida-nextcloud) chown -R root:root /usr/local/fd/fairdata-download/dev_config/settings.cfg

echo "Starting FPM..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) mkdir /run/php-fpm
docker exec -it $(docker ps -q -f name=ida-nextcloud) php-fpm

echo "Starting Apache..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /sbin/httpd -k start

echo "Creating database $DBNAME..."
docker exec -it $(docker ps -q -f name=ida-db) psql -U "$DBUSER" -c "CREATE DATABASE $DBNAME;"

echo "Installing Nextcloud..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) chown -R $HTTPD_USER:$HTTPD_USER /var/ida/nextcloud/config
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) cp /var/ida/nextcloud/.htaccess /tmp/.htaccess
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) php /var/ida/nextcloud/occ maintenance:install --database $DBTYPE --database-name $DBNAME --database-host $DBHOST --database-user $DBUSER --database-pass $DBPASSWORD --admin-user $NC_ADMIN_USER --admin-pass $NC_ADMIN_PASS --data-dir $STORAGE_OC_DATA_ROOT
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) mv /tmp/.htaccess /var/ida/nextcloud/.htaccess

echo "Installing Nextcloud config.php..."
docker cp ../fairdata-docker/ida/config/config.dev.php $(docker ps -q -f name=ida-nextcloud):/var/ida/nextcloud/config/config.php
docker exec -it $(docker ps -q -f name=ida-nextcloud) chown -R $HTTPD_USER:$HTTPD_USER /var/ida/nextcloud/config

echo "Fixing IDA file permissions..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /var/ida/utils/fix-permissions

echo "Re-starting Apache..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /sbin/httpd -k stop
docker exec -it $(docker ps -q -f name=ida-nextcloud) /sbin/httpd -k start

echo "Disabling unused Nextcloud apps..."
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) /var/ida/utils/disable_nextcloud_apps > /dev/null

echo "Enabling essential Nextcloud apps..."
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) php /var/ida/nextcloud/occ app:enable files_sharing > /dev/null
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) php /var/ida/nextcloud/occ app:enable admin_audit > /dev/null
docker exec -u $HTTPD_USER -it $(docker ps -q -f name=ida-nextcloud) php /var/ida/nextcloud/occ app:enable ida > /dev/null

echo "Configuring essential Nextcloud settings..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /var/ida/utils/initialize_nextcloud_settings > /dev/null

echo "Configuring Nextcloud cronjob..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /var/ida/utils/initialize_nextcloud_cronjob > /dev/null

echo "Adding optimization indices to database..."
docker cp ./utils/create_db_indices.pgsql $(docker ps -q -f name=ida-db):/tmp/create_db_indices.pgsql
docker exec -it $(docker ps -q -f name=ida-db) psql -U $DBUSER -f /tmp/create_db_indices.pgsql $DBNAME > /dev/null

echo "Initializing python3 virtual environments..."
echo "- IDA postprocessing agents"
docker exec -it $(docker ps -q -f name=ida-nextcloud) /var/ida/utils/initialize_venv > /dev/null
echo "- IDA command line tools"
docker exec -it $(docker ps -q -f name=ida-nextcloud) /var/ida-tools/tests/utils/initialize-venv > /dev/null
echo "- IDA statdb reports"
docker exec -it $(docker ps -q -f name=ida-nextcloud) /opt/fairdata/ida-report/utils/initialize-venv > /dev/null
echo "- IDA admin portal"
docker exec -it $(docker ps -q -f name=ida-nextcloud) /opt/fairdata/ida-admin-portal/utils/initialize-venv > /dev/null
echo "- IDA healthcheck service"
docker exec -it $(docker ps -q -f name=ida-nextcloud) /usr/local/fd/fairdata-ida-healthcheck/utils/initialize-venv > /dev/null
echo "- Fairdata download service"
docker exec -it $(docker ps -q -f name=ida-nextcloud) /usr/local/fd/fairdata-download/utils/initialize-venv > /dev/null

echo "Initializing rabbitmq..."
APP_ROOT=/var/ida
APP_VENV=$APP_ROOT/venv
docker exec -e VIRTUAL_ENV=$APP_VENV -w $APP_ROOT -it $(docker ps -q -f name=ida-nextcloud) $APP_VENV/bin/python -m agents.utils.rabbitmq > /dev/null
docker exec -it $(docker ps -q -f name=ida-rabbitmq) rabbitmqctl delete_user download &>/dev/null
docker exec -it $(docker ps -q -f name=ida-rabbitmq) rabbitmqctl delete_vhost download &>/dev/null
docker exec -it $(docker ps -q -f name=ida-rabbitmq) rabbitmqctl add_user download download
docker exec -it $(docker ps -q -f name=ida-rabbitmq) rabbitmqctl add_vhost download
docker exec -it $(docker ps -q -f name=ida-rabbitmq) rabbitmqctl set_permissions -p download download '.*' '.*' '.*'
docker exec -it $(docker ps -q -f name=ida-rabbitmq) rabbitmqctl set_user_tags download management

echo "Initializing download service..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /usr/local/fd/fairdata-download/utils/initialize-docker > /dev/null

echo "Starting IDA postprocessing agents..."
docker exec -u $HTTPD_USER --detach -e VIRTUAL_ENV=$APP_VENV -w $APP_ROOT $(docker ps -q -f name=ida-nextcloud) $APP_VENV/bin/python -m agents.metadata.metadata_agent
docker exec -u $HTTPD_USER --detach -e VIRTUAL_ENV=$APP_VENV -w $APP_ROOT $(docker ps -q -f name=ida-nextcloud) $APP_VENV/bin/python -m agents.replication.replication_agent

echo "Starting IDA admin portal..."
APP_ROOT=/opt/fairdata/ida-admin-portal
docker exec --detach -e APP_ROOT=$APP_ROOT -w $APP_ROOT $(docker ps -q -f name=ida-nextcloud) $APP_ROOT/ida-admin-portal.sh

echo "Starting IDA healthcheck service..."
APP_ROOT=/usr/local/fd/fairdata-ida-healthcheck
APP_VENV=$APP_ROOT/venv
docker exec --detach -e APP_ROOT=$APP_ROOT -e VIRTUAL_ENV=$APP_VENV -w $APP_ROOT $(docker ps -q -f name=ida-nextcloud) $APP_VENV/bin/python -m wsgi

echo "Starting download service..."
APP_ROOT=/usr/local/fd/fairdata-download
docker exec -u download --detach -e APP_ROOT=$APP_ROOT -w $APP_ROOT $(docker ps -q -f name=ida-nextcloud) $APP_ROOT/dev_config/fairdata-download.sh
docker exec -u download --detach -e APP_ROOT=$APP_ROOT -w $APP_ROOT $(docker ps -q -f name=ida-nextcloud) $APP_ROOT/dev_config/fairdata-download-generator.docker.sh

echo "Initializing test accounts..."
docker exec -it $(docker ps -q -f name=ida-nextcloud) /opt/fairdata/fairdata-test-accounts/initialize-test-accounts fd_test_ida_project
docker exec -it $(docker ps -q -f name=ida-nextcloud) /opt/fairdata/fairdata-test-accounts/initialize-test-accounts fd_test_download_project
