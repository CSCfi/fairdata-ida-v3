<?php
$CONFIG = array (
  'passwordsalt' => '****',
  'secret' => '****',
  'instanceid' => '****',
  'version' => '30.0.1.2',
  'installed' => true,
  'trusted_domains' => array (
    0 => 'LOCAL_SERVER_FQDN',
  ),
  'datadirectory' => '/mnt/storage_vol01/ida',
  'logfile' => '/mnt/storage_vol01/log/nextcloud.log',
  // 0: DEBUG: All activity; the most detailed logging
  // 1: INFO:  Activity such as user logins and file activities, plus warnings, errors, and fatal errors
  // 2: WARN:  Operations succeed, but with warnings of potential problems, plus errors and fatal errors
  // 3: ERROR: An operation fails, but other services and operations continue, plus fatal errors
  // 4: FATAL: The server stops
  'loglevel' => 0, 
  'log_rotate_size' => 0,
  'overwrite.cli.url' => 'https://LOCAL_SERVER_FQDN',
  'dbtype' => 'pgsql',
  'dbname' => 'nextcloud30',
  'dbhost' => 'DEFINE_ME',
  'dbport' => '',
  'dbtableprefix' => 'oc_',
  'dbuser' => 'nextcloud',
  'dbpassword' => 'DEFINE_ME',
  'htaccess.RewriteBase' => '/',
  'theme' => 'ida',
  'knowledgebaseenabled' => false,
  'auth.bruteforce.protection.enabled' => false,
  'enable_avatars' => false,
  'allow_user_to_change_display_name' => false,
  'skeletondirectory' => '',
  'updatechecker' => false,
  'upgrade.disable-web' => true,
  'appstoreenabled' => false,
  'enable_previews' => false,
  'cron_log' => true,
  'maintenance' => false,
  'integrity.check.disabled' => true,
  'filelocking.enabled' => false,
  'apps_paths' => array (
    0 =>
    array (
      'path' => '/var/ida/nextcloud/apps',
      'url' => '/apps',
      'writable' => true,
    ),
  ),
  
  'gs.enabled' => false,

  'ida' => array (
    'IDA_ENVIRONMENT' => 'DEV',
    'BATCH_ACTION_TOKEN' => 'DEFINE_ME',
    'PROJECT_USER_PASS' => 'DEFINE_ME',
    'RABBIT_HOST' => 'DEFINE_ME',
    'RABBIT_PORT' => 5672,
    'RABBIT_VHOST' => 'ida-vhost',
    'RABBIT_WORKER_USER' => 'worker',
    'RABBIT_WORKER_PASS' => 'DEFINE_ME',
    'FILE_API' => 'https://LOCAL_SERVER_FQDN/remote.php/webdav',
    'SHARE_API' => 'https://LOCAL_SERVER_FQDN/ocs/v1.php/apps/files_sharing/api/v1/shares',
    'GROUP_API' => 'https://LOCAL_SERVER_FQDN/ocs/v1.php/cloud/groups',
    'SIMULATE_AGENTS' => false,
    // v1
    'METAX_API' => 'https://DEFINE_ME/rest/v1',
    'METAX_RPC' => 'https://DEFINE_ME/rpc/v1',       // deprecated from Metax v3 onwards
    'METAX_USER' => 'ida',                           // deprecated from Metax v3 onwards
    'METAX_PASS' => 'DEFINE_ME',
    // v3
    //'METAX_API' => 'https://DEFINE_ME/v3',
    //'METAX_PASS' => 'DEFINE_ME',
  ),
  'IDA_HOME' => 'https://LOCAL_SERVER_FQDN',
  'LOCAL_LOGIN' => true,
  'SSO_AUTHENTICATION' => true,
  'SSO_API' => 'https://DEFINE_ME',
  'SSO_DOMAIN' => 'fd-dev.csc.fi',
  'SSO_KEY' => 'DEFINE_ME',
  'SSO_PASSWORD' => 'DEFINE_ME',
  'FDWE_URL' => 'https://DEFINE_ME/fdwe.js',
  'memcache.local' => '\\OC\\Memcache\\Redis',
  'memcache.distributed' => '\\OC\\Memcache\\Redis',
  'redis' => array (
    'host' => '127.0.0.1',
    'port' => 6379,
  ),
);
