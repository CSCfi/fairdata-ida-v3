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

import importlib.util
import sys
import os
import time
import requests
import logging
import psycopg2
import dateutil.parser
from datetime import datetime
from hashlib import sha256
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Use UTC
os.environ['TZ'] = 'UTC'
time.tzset()

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

LOG_ENTRY_FORMAT = '%(asctime)s %(filename)s (%(process)d) %(levelname)s %(message)s'
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
NULL_VALUES      = [ None, 0, '', False, 'None', 'null', 'false' ]


def load_configuration(filesystem_pathname):
    """
    Load and return all defined variables from the specified configuration file
    """

    module_name = 'config.variables'
    
    try:
        # python versions >= 3.5
        module_spec = importlib.util.spec_from_file_location(module_name, filesystem_pathname)
        config = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(config)
    except AttributeError:
        # python versions < 3.5
        from importlib.machinery import SourceFileLoader
        config = SourceFileLoader(module_name, filesystem_pathname).load_module()

    # Define Metax version if Metax URL defined

    if config.METAX_API:
        if '/rest/' in config.METAX_API:
            config.METAX_API_VERSION = 1
        else:
            config.METAX_API_VERSION = 3

    # Allow environment setting to override configuration or defaults for debug output

    if os.environ.get('DEBUG'):
        config.DEBUG = os.environ['DEBUG']
    if os.environ.get('DEBUG_VERBOSE'):
        config.DEBUG_VERBOSE = os.environ['DEBUG_VERBOSE']

    # Normalize string values to booleans and set defaults if not defined

    if hasattr(config, 'DEBUG') and isinstance(config.DEBUG, str) and config.DEBUG.lower() == 'true':
        config.DEBUG = True
    else:
        config.DEBUG = False

    if hasattr(config, 'DEBUG_VERBOSE') and isinstance(config.DEBUG_VERBOSE, str) and config.DEBUG_VERBOSE.lower() == 'true':
        config.DEBUG_VERBOSE = True
    else:
        config.DEBUG_VERBOSE = False

    return config


def generate_checksum(filesystem_pathname):
    if not os.path.isfile(filesystem_pathname):
        sys.stderr.write("ERROR: Pathname %s not found or not a file\n" % filesystem_pathname)
        return None
    try:
        block_size = 65536
        sha = sha256()
        with open(filesystem_pathname, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha.update(block)
        checksum = str(sha.hexdigest()).lower()
    except Exception as e:
        sys.stderr.write("ERROR: Failed to generate checksum for %s: %s\n" % (filesystem_pathname, str(e)))
        return None
    return checksum


def normalize_timestamp(timestamp):
    """
    Returns the input timestamp as a normalized Canonical ISO 8601 UTC timestamp string YYYY-MM-DDThh:mm:ssZ
    """

    # Sniff the input timestamp value and convert to a datetime instance as needed
    if isinstance(timestamp, str):
        timestamp = datetime.utcfromtimestamp(dateutil.parser.parse(timestamp).timestamp())
    elif isinstance(timestamp, float) or isinstance(timestamp, int):
        timestamp = datetime.utcfromtimestamp(timestamp)
    elif not isinstance(timestamp, datetime):
        raise Exception("Invalid timestamp value")

    # Return the normalized ISO UTC timestamp string
    return timestamp.strftime(TIMESTAMP_FORMAT)


def generate_timestamp():
    """
    Get current time as normalized ISO 8601 UTC timestamp string
    """
    return normalize_timestamp(datetime.utcnow().replace(microsecond=0))


def get_project_pathname(project, pathname):
    if pathname.startswith('staging/'):
        return "/%s+/%s" % (project, pathname[8:])
    else:
        return "/%s/%s" % (project, pathname[7:])



def get_last_add_change_timestamps(config):
    """
    Retrieve all latest 'add' change events for the project + file relative pathname, in staging,
    from the changes database table, as a dictionary with pathname as key and timestamp as value
    (used to determine upload timestamp when not recorded explicitly in the Nextcloud cache)
    """

    logging.debug("get_last_add_change_timestamps project = %s" % config.PROJECT)

    conn = psycopg2.connect(database=config.DBNAME,
                            user=config.DBROUSER,
                            password=config.DBROPASSWORD,
                            host=config.DBHOST,
                            port=config.DBPORT)

    cur = conn.cursor()

    staging_pathname_prefix = "/%s%s/%%" % (config.PROJECT, config.STAGING_FOLDER_SUFFIX)

    query = "WITH latest_timestamps AS ( \
                SELECT DISTINCT ON (project, change, pathname) \
                    project, change, pathname, timestamp \
                FROM {}ida_data_change \
                WHERE project = %s \
                AND change = 'add' \
                AND pathname LIKE %s \
                ORDER BY project, change, pathname, timestamp DESC \
             ) \
             SELECT pathname, timestamp  \
             FROM latest_timestamps".format(config.DBTABLEPREFIX)
    
    logging.debug("get_last_add_change_timestamps query = %s" % query)

    cur.execute(query, (config.PROJECT, staging_pathname_prefix))

    rows = cur.fetchall()

    logging.debug("get_last_add_change_timestamps rows = %d" % len(rows))

    add_events = {}

    for row in rows:
        logging.debug("get_last_add_change_timestamps timestamp = %s pathname = %s" % (row[1], row[0]))
        add_events[row[0]] = row[1]

    return add_events


def get_last_add_change_timestamp(config, pathname):
    """
    Retrieve the latest 'add' change event for the project + file relative pathname, in staging,
    from the changes database table, as a normalized ISO timestamp string, else return None
    (used to determine upload timestamp when not recorded explicitly in the Nextcloud cache)
    """

    logging.debug("get_last_add_change_timestamp project = %s pathname = %s" % (config.PROJECT, pathname))

    conn = psycopg2.connect(database=config.DBNAME,
                            user=config.DBROUSER,
                            password=config.DBROPASSWORD,
                            host=config.DBHOST,
                            port=config.DBPORT)

    cur = conn.cursor()

    staging_pathname = "/%s%s%s" % (config.PROJECT, config.STAGING_FOLDER_SUFFIX, pathname)

    logging.debug("get_last_add_change_timestamp staging_pathname = %s" % staging_pathname)

    query = "SELECT timestamp FROM {}ida_data_change \
             WHERE project = %s \
             AND change = 'add' \
             AND pathname = %s \
             ORDER BY timestamp DESC LIMIT 1".format(config.DBTABLEPREFIX)

    logging.debug("get_last_add_change_timestamp query = %s" % query)

    cur.execute(query, (config.PROJECT, staging_pathname))

    rows = cur.fetchall()

    logging.debug("get_last_add_change_timestamp rows = %d" % len(rows))

    if len(rows) == 1:
        timestamp = rows[0][0]
        logging.debug("get_last_add_change_timestamp timestamp = %s" % timestamp)
        return timestamp

    return None


def log_and_output(config, level, message):
    try:
        logging.log(level, message)
        if not config.QUIET:
            sys.stderr.write("%s %s\n" % (generate_timestamp(), message))
    except Exception as logerror:
            sys.stderr.write("ERROR: %s\n" % str(logerror))
