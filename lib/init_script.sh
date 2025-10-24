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
# Ensure script is run as apache

ID=$(id -u -n)
if [ "$ID" != "apache" ]; then
    sudo -u apache bash "$0" "$@"
    exit
fi

#--------------------------------------------------------------------------------
# Verify needed utilities are available

for NEEDS_PROG in curl php python3.12 realpath jq
do
    PROG_LOCATION=$(/usr/bin/which $NEEDS_PROG 2>/dev/null)
    if [ ! -e "$PROG_LOCATION" ]; then
        echo "Can't find $NEEDS_PROG in your \$PATH"
        exit 1
    fi
done

#--------------------------------------------------------------------------------
# Load service constants and configuration settings

INIT_SCRIPT_PATHNAME=$(realpath "${BASH_SOURCE[0]}")
INIT_SCRIPT_DIR=$(dirname "$INIT_SCRIPT_PATHNAME")
INIT_SCRIPT=$(basename "$INIT_SCRIPT_PATHNAME")
ROOT=$(dirname "$INIT_SCRIPT_DIR")

CONSTANTS_FILE="$ROOT/lib/constants.sh"

if [ -e $CONSTANTS_FILE ]
then
    . $CONSTANTS_FILE
else
    echo "The service constants file $CONSTANTS_FILE cannot be found. Aborting." >&2
    exit 1
fi

CONFIG_FILE="$ROOT/config/config.sh"

# Allow environment setting to override configuration for debug output
if [ "$DEBUG" != "" ]; then
    ENV_DEBUG="$DEBUG"
fi

if [ -e $CONFIG_FILE ]
then
    . $CONFIG_FILE
else
    echo "The configuration file $CONFIG_FILE cannot be found. Aborting." >&2
    exit 1
fi

if [ "$ENV_DEBUG" ]; then
    DEBUG="$ENV_DEBUG"
    unset ENV_DEBUG
fi

if [ "$DEBUG" = "" ]; then
    DEBUG="false"
fi

#--------------------------------------------------------------------------------
# Set umask to limit filesystem access to owner and group to be more secure

umask 007

#--------------------------------------------------------------------------------
# Common initialization for all scripts

CURL_OPS="--fail -k -s -S"
CURL_GET="curl $CURL_OPS"
CURL_POST="curl $CURL_OPS -X POST"
CURL_DELETE="curl $CURL_OPS -X DELETE"
CURL_MKCOL="curl $CURL_OPS -X MKCOL"
CURL_PATCH="curl $CURL_OPS -X PATCH"

IDA_HEADERS="-H \"OCS-APIRequest: true\" -H \"IDA-Mode: System\""
IDA_MODE_HEADER="IDA-Mode: System"

TODAY=$(date -u +"%Y-%m-%d")
START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

PROCESSID="$$"

if [ "$DEBUG" = "true" ]; then
    echo "--- $PROCESSID $SCRIPT ---"
    echo "START: $START"
fi

#--------------------------------------------------------------------------------
# Initialize log and tmp folders, if necessary...

LOGS=$(dirname "$LOG")

if [ ! -d $LOGS ]; then
    mkdir -p $LOGS 2>/dev/null
fi

if [ ! -d $LOGS ]; then
    echo "Error: Can't initialize log folder: \"$LOGS\"" >&2
    exit 1
fi

if [ "$TMPDIR" = "" ]; then
    TMPDIR=/tmp
fi

if [ ! -d "$TMPDIR" ]; then
    mkdir -p $TMPDIR
fi

if [ ! -d $TMPDIR ]; then
    echo "Error: Can't initialize temporary folder: \"$TMPDIR\"" >&2
    exit 1
fi

#--------------------------------------------------------------------------------
# Initialize log file and record start of script execution

if [ ! -e $LOG ]; then
    touch $LOG
    if [ "$?" -ne 0 ]; then
        echo "Can't create log file \"$LOG\"" >&2
        exit 1
    fi
fi

OUT=$(echo "$START $SCRIPT ($PROCESSID) START $@" 2>/dev/null >>"$LOG")
if [ "$?" -ne 0 ]; then
    echo "Can't write to log file \"$LOG\"" >&2
    exit 1
fi

#--------------------------------------------------------------------------------
# Common functions for all scripts

function urlEncode() {
    jq -rn --arg v "$1" '$v|@uri'
}

function addToLog () {
    MSG=$(echo "$@" | tr '\n' ' ')
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$TIMESTAMP $SCRIPT ($PROCESSID) $MSG" 2>/dev/null >>"$LOG"
    sync
    sleep 0.1
}

function echoAndLog () {
    MSG=$(echo "$@" | tr '\n' ' ')
    echo "$MSG"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$TIMESTAMP $SCRIPT ($PROCESSID) $MSG" 2>/dev/null >>"$LOG"
    sync
    sleep 0.1
}

function errorExit () {
    MSG=$(echo "$@" | tr '\n' ' ')
    echo "$MSG" >&2
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$TIMESTAMP $SCRIPT ($PROCESSID) FATAL ERROR $MSG" >>"$LOG"
    sync
    sleep 0.1
    exit 1
}

function testUserLogin () {

    USERNAME="$1"
    PASSWORD="$2"

    if [ "$DEBUG" = "true" ]; then
        echo "curl -u $USERNAME:*** $CURL_OPS -I -w '%{http_code}' -o /dev/null \"${FILE_API}/\"" >&2
    fi

    OUTPUT=$(curl -u $USERNAME:$PASSWORD $CURL_OPS -I -w '%{http_code}' -o /dev/null "${FILE_API}/" 2>&1)

    if [[ ${OUTPUT::1} != "2" ]]; then
        echo "NOK"
    else
        echo "OK"
    fi
}
