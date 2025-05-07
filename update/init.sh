# Strict assumptions are made about the location of necessary scripts; update if/as needed.

START=`date -u +"%Y-%m-%dT%H:%M:%SZ"`
SCRIPT=$(basename $0)

. /var/ida/config/config.sh

# Ensure IDA_UPDATE_ROOT is defined in configuration and exists
if [ -z "$IDA_UPDATE_ROOT" ]; then
    echo "The environment variable IDA_UPDATE_ROOT must be defined. Aborting." >&2
    exit 1
fi
if [ ! -d "$IDA_UPDATE_ROOT" ]; then
    echo "The directory $IDA_UPDATE_ROOT does not exist. Aborting." >&2
    exit 1
fi

# Ensure DBNAME_NEW and DBNAME_OLD are defined in configuration and are not the same
if [[ -z "$DBNAME_NEW" ]]; then
  echo "Error: Environment variable DBNAME_NEW must be defined" >&2
  exit 1
fi
if [[ -z "$DBNAME_OLD" ]]; then
  echo "Error: Environment variable DBNAME_OLD must be defined" >&2
  exit 1
fi
if [[ "$DBNAME_NEW" = "$DBNAME_OLD" ]]; then
  echo "Error: Environment variables DBNAME_NEW and DBNAME_OLD cannot be the same" >&2
  exit 1
fi

# Ensure DBHOST, DBPORT, DBUSER, DBPASSWORD, DBROUSER, and DBROPASSWORD are all defined in configuration
if [[ -z "$DBHOST" ]]; then
  echo "Error: Environment variable DBHOST must be defined" >&2
  exit 1
fi
if [[ -z "$DBPORT" ]]; then
  echo "Error: Environment variable DBPORT must be defined" >&2
  exit 1
fi
if [[ -z "$DBUSER" ]]; then
  echo "Error: Environment variable DBUSER must be defined" >&2
  exit 1
fi
if [[ -z "$DBPASSWORD" ]]; then
  echo "Error: Environment variable DBPASSWORD must be defined" >&2
  exit 1
fi
if [[ -z "$DBROUSER" ]]; then
  echo "Error: Environment variable DBROUSER must be defined" >&2
  exit 1
fi
if [[ -z "$DBROPASSWORD" ]]; then
  echo "Error: Environment variable DBROPASSWORD must be defined" >&2
  exit 1
fi

# Ensure FAIRDATA_TEST_ACCOUNTS is defined in configuration
if [[ -z "$FAIRDATA_TEST_ACCOUNTS" ]]; then
  echo "Error: Environment variable FAIRDATA_TEST_ACCOUNTS must be defined" >&2
  exit 1
fi

if [ "$IDA_ENVIRONMENT" = "DEV" ]; then

    PROJECTS="fd_test_ida_project \
              fd_test_multiuser_project \
              fd_test_multiproject_a \
              fd_test_multiproject_b \
              fd_large_file_project \
              fd_user1_project"

    USERS="fd_test_ida_user \
           fd_test_multiuser_a \
           fd_test_multiuser_b \
           fd_test_multiuser_c \
           fd_test_multiproject_user_a \
           fd_test_multiproject_user_b \
           fd_test_multiproject_user_ab \
           fd_large_file_user \
           fd_user1 \
           PSO_fd_test_ida_project \
           PSO_fd_test_multiuser_project \
           PSO_fd_test_multiproject_a \
           PSO_fd_test_multiproject_b \
           PSO_fd_large_file_project \
           PSO_fd_user1_project"

    LARGE_PROJECTS="fd_large_file_project"
    INTERNAL_PROJECTS="fd_user1_project"
    INTERNAL_USERS="PSO_fd_user1_project fd_user1"
else
    PROJECTS=$(/var/ida/update/list-projects)
    USERS=$(/var/ida/update/list-users)
    INTERNAL_PROJECTS="$INTERNAL_PROJECTS 2011020"
    INTERNAL_USERS="$INTERNAL_USERS PSO_2011020 ida-test-user"
fi

# Initialize migration specific variables
DATAROOT="$IDA_UPDATE_ROOT/data"
OLDDATA="$DATAROOT/old"
NEWDATA="$DATAROOT/new"
DBDATA="$DATAROOT/db"
DIFFS="$DATAROOT/diff"
TMPDIR="$IDA_UPDATE_ROOT/tmp"
LOGDIR="$IDA_UPDATE_ROOT/log"
LOG="${LOGDIR}/${START}-${SCRIPT}.log"

if [ ! -d "$TMPDIR" ]; then
    mkdir -p "$TMPDIR"
fi

if [ ! -d "$LOGDIR" ]; then
    mkdir -p "$LOGDIR"
fi

ERR="${TMPDIR}/${SCRIPT}.err"
cleanup() {
    rm -f "$ERR" 2>/dev/null
}
trap cleanup EXIT

function errorExit {
    MSG=`echo "$@" | tr '\n' ' '`
    echo "$MSG" >&2
    sync
    sleep 0.1
    exit 1
}

TABLES="oc_accounts \
        oc_accounts_data \
        oc_filecache \
        oc_filecache_extended \
        oc_groups \
        oc_group_user \
        oc_ida_action \
        oc_ida_data_change \
        oc_ida_frozen_file \
        oc_mimetypes \
        oc_mounts \
        oc_preferences \
        oc_share \
        oc_storages \
        oc_users"

OC_ACCOUNTS_FIELDS='uid,data'
OC_ACCOUNTS_DATA_FIELDS='uid,name,value'
OC_FILECACHE_FIELDS='fileid,storage,path,path_hash,parent,name,mimetype,mimepart,size,mtime,storage_mtime,encrypted,unencrypted_size,etag,permissions,checksum'
OC_FILECACHE_EXTENDED_FIELDS='fileid,metadata_etag,creation_time,upload_time'
OC_GROUPS_FIELDS='gid,displayname'
OC_GROUP_USER_FIELDS='gid,uid'
OC_IDA_ACTION_FIELDS='id,pid,action,project,"user",node,pathname,initiated,storage,pids,checksums,metadata,replication,completed,failed,cleared,error,retry,retrying'
OC_IDA_ACTION_FIELDS_TEST='id,pid,action,project,"user",node,nodetype,filecount,pathname,initiated,storage,pids,checksums,metadata,replication,completed,failed,cleared,error,retry,retrying'
OC_IDA_DATA_CHANGE_FIELDS='id,timestamp,project,"user",change,pathname,target,mode'
OC_IDA_FROZEN_FILE_FIELDS='id,node,pathname,action,project,pid,size,checksum,modified,frozen,metadata,replicated,removed,cleared'
OC_MIMETYPES_FIELDS='id,mimetype'
OC_MOUNTS_FIELDS='id,storage_id,root_id,user_id,mount_point,mount_id'
OC_PREFERENCES_FIELDS='userid,appid,configkey,configvalue'
OC_SHARE_FIELDS='id,share_type,share_with,uid_owner,uid_initiator,parent,item_type,item_source,item_target,file_source,file_target,permissions,stime,accepted,expiration,token,mail_send,share_name,hide_download,label'
OC_STORAGES_FIELDS='numeric_id,id,available,last_checked'
OC_USERS_FIELDS='uid,displayname,uid_lower'

# sequence:table:column
SEQUENCES=(
    "oc_filecache_fileid_seq:oc_filecache:fileid"
    "oc_storages_numeric_id_seq:oc_storages:numeric_id"
    "oc_share_id_seq:oc_share:id"
    "oc_ida_action_id_seq:oc_ida_action:id"
    "oc_ida_data_change_id_seq:oc_ida_data_change:id"
    "oc_ida_frozen_file_id_seq:oc_ida_frozen_file:id"
    "oc_mounts_id_seq:oc_mounts:id"
    "oc_mimetypes_id_seq:oc_mimetypes:id"
)

TEST_MIMETYPES="application/x-test1-does-not-exist text/x-test2-does-not-exist image/x-test3-does-not-exist"

FILE_ENDINGS=".actions.pending.json \
              .actions.failed.json \
              .actions.cleared.json \
              .actions.completed.json \
              .actions.incomplete.json \
              .actions.initiating.json \
              .action.files.json \
              .changes.json \
              .inventory.json \
              .stats.txt \
              .status.txt"

#--------------------------------------------------------------------------------

# Redirect both stdout and stderr to log
exec > >(stdbuf -oL tee "$LOG") 2>&1 
sync

if [ ! "$SILENT" ]; then
    echo "$START $SCRIPT $IDA_ENVIRONMENT"
fi

OCC="sudo -u apache php /var/ida/nextcloud/occ"
