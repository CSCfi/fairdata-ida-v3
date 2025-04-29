<?php
/**
 * This file is part of the Fairdata IDA research data storage service.
 *
 * Copyright (C) 2018 Ministry of Education and Culture, Finland
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License,
 * or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
 * License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * @author    CSC - IT Center for Science Ltd., Espoo Finland <servicedesk@csc.fi>
 * @license   GNU Affero General Public License, version 3
 * @link      https://www.fairdata.fi/en/ida
 */

declare(strict_types=1);

namespace OCA\IDA\AppInfo;

use OCA\IDA\Controller\ViewController;
use OCA\IDA\Controller\ActionController;
use OCA\IDA\Controller\FrozenFileController;
use OCA\IDA\Controller\FreezingController;
use OCA\IDA\Controller\DataChangeController;
use OCA\IDA\Db\ActionMapper;
use OCA\IDA\Db\FrozenFileMapper;
use OCA\IDA\Db\DataChangeMapper;
use OCA\IDA\View\Navigation;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\DB\Exception as DBException;
use OCP\IDBConnection;
use OCP\IUserSession;
use OCP\IAppConfig;
use OCP\IConfig;
use OCP\IRequest;
use OCP\IURLGenerator;
use Psr\Log\LoggerInterface;

/**
 * IDA Nextcloud App
 */
class Application extends App implements IBootstrap {

    public const APP_ID = 'ida';

    protected IDBConnection $dbConnection;
    protected IConfig $config;
    protected IAppConfig $appConfig;
    protected LoggerInterface $logger;
    protected string $dbPrefix;

	public function __construct(array $urlParams = []) {
		parent::__construct(self::APP_ID, $urlParams);
        $this->dbConnection = \OC::$server->get(IDBConnection::class);
        $this->config = \OC::$server->get(IConfig::class);
        $this->appConfig = \OC::$server->get(IAppConfig::class);
        $this->logger = \OC::$server->get(LoggerInterface::class);
        $this->dbPrefix = $this->config->getSystemValue('dbtableprefix', 'oc_');
    }

    /**
     * Register services and dependencies
     *
     * @param IRegistrationContext $context
     */
    public function register(IRegistrationContext $context): void {

        //$this->logger->debug('INIT - Registering IDA app components...');

        require_once __DIR__ . '/../../vendor/autoload.php';

        $context->registerService('CurrentUID', function($c) {
            $user = $c->query(IUserSession::class)->getUser();
            return $user ? $user->getUID() : '';
        });

        $context->registerService('Navigation', function($c) {
            return new Navigation(
                $c->query(IURLGenerator::class)
            );
        });

        $context->registerService('ActionMapper', function($c) {
            return new ActionMapper(
                $c->query(IDBConnection::class),
                $c->query(IConfig::class),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('FrozenFileMapper', function($c) {
            return new FrozenFileMapper(
                $c->query(IDBConnection::class),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('DataChangeMapper', function($c) {
            return new DataChangeMapper(
                $c->query(IDBConnection::class),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('ActionController', function($c) {
            return new ActionController(
                $c->query('AppName'),
                $c->query(IRequest::class),
                $c->query('ActionMapper'),
                $c->query('CurrentUID'),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('FrozenFileController', function($c) {
            return new FrozenFileController(
                $c->query('AppName'),
                $c->query(IRequest::class),
                $c->query('FrozenFileMapper'),
                $c->query('CurrentUID'),
                $c->query(IConfig::class),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('FreezingController', function($c) {
            return new FreezingController(
                $c->query('AppName'),
                $c->query(IRequest::class),
                $c->query('ActionMapper'),
                $c->query('FrozenFileMapper'),
                $c->query('DataChangeMapper'),
                $c->query('CurrentUID'),
                $c->query(IConfig::class),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('ViewController', function($c) {
            return new ViewController(
                $c->query('AppName'),
                $c->query(IRequest::class),
                $c->query('ActionMapper'),
                $c->query('FrozenFileMapper'),
                $c->query('FreezingController'),
                $c->query('CurrentUID'),
                $c->query('Navigation'),
                $c->query(LoggerInterface::class)
            );
        });

        $context->registerService('DataChangeController', function($c) {
            return new DataChangeController(
                $c->query('AppName'),
                $c->query(IRequest::class),
                $c->query('DataChangeMapper'),
                $c->query('CurrentUID'),
                $c->query(IConfig::class),
                $c->query(LoggerInterface::class)
            );
        });
    }

    /**
     * Boot the application, initialize navigation and load scripts
     *
     * @param IBootContext $context
     */
    public function boot(IBootContext $context): void {

        // Ensure all IDA database tables and indices exist
        $this->initializeDatabase();

        // Load Scripts and Styles
        \OCP\Util::addScript(self::APP_ID, 'ida-constants');
        \OCP\Util::addScript(self::APP_ID, 'ida-utils');
        \OCP\Util::addScript(self::APP_ID, 'ida-actions');
        \OCP\Util::addScript(self::APP_ID, 'ida-ui');
        \OCP\Util::addScript(self::APP_ID, 'ida-firstrunwizard');
    }

    /**
     * Ensure all IDA database tables and indices exist
     */
    private function initializeDatabase() {
        try {
            $initialized = $this->appConfig->getValueBool(self::APP_ID, 'database_initialized', false);

            // Only run the table creation logic if not already done
            if ($initialized != true) {
                $this->logger->info('INIT - Initializing IDA database...');
                $this->createTables();
                $this->createIndices();
                $this->appConfig->setValueBool(self::APP_ID, 'database_initialized', true);
            }
            //$this->logger->debug('INIT - IDA database initialized.');
        } catch (DBException $e) {
            $this->logger->error('INIT - Failed to initialize database: ' . $e->getMessage());
        }
    }

    private function createTables() {
        $this->createTable_ida_action();
        $this->createTable_ida_frozen_file();
        $this->createTable_ida_data_change();
    }

    private function createTable_ida_action() {
        $sql = 'CREATE TABLE IF NOT EXISTS ' . $this->dbPrefix . 'ida_action (
            "id"          SERIAL PRIMARY KEY,
            "pid"         TEXT NOT NULL,
            "action"      TEXT NOT NULL,
            "project"     TEXT NOT NULL,
            "user"        TEXT NOT NULL,
            "pathname"    TEXT NOT NULL,
            "node"        INTEGER DEFAULT 0 NOT NULL,
            "nodetype"    TEXT CHECK ("nodetype" IN (\'folder\', \'file\')),
            "filecount"   INTEGER,
            "initiated"   TEXT NOT NULL,
            "storage"     TEXT,
            "pids"        TEXT,
            "checksums"   TEXT,
            "metadata"    TEXT,
            "replication" TEXT,
            "completed"   TEXT,
            "failed"      TEXT,
            "cleared"     TEXT,
            "error"       TEXT,
            "retry"       TEXT,
            "retrying"    TEXT
        )';
        $this->dbConnection->executeStatement($sql);
    }

    private function createTable_ida_frozen_file() {
        $sql = 'CREATE TABLE IF NOT EXISTS ' . $this->dbPrefix . 'ida_frozen_file (
            "id"         SERIAL PRIMARY KEY,
            "node"       INTEGER DEFAULT 0 NOT NULL,
            "pathname"   TEXT NOT NULL,
            "action"     TEXT NOT NULL,
            "project"    TEXT NOT NULL,
            "pid"        TEXT,
            "size"       BIGINT,
            "checksum"   TEXT,
            "modified"   TEXT,
            "frozen"     TEXT,
            "metadata"   TEXT,
            "replicated" TEXT,
            "removed"    TEXT,
            "cleared"    TEXT
        )';
        $this->dbConnection->executeStatement($sql);
    }

    private function createTable_ida_data_change() {
        $sql = 'CREATE TABLE IF NOT EXISTS ' . $this->dbPrefix . 'ida_data_change (
            "id"        SERIAL PRIMARY KEY,
            "timestamp" TEXT NOT NULL,
            "project"   TEXT NOT NULL,
            "user"      TEXT NOT NULL,
            "change"    TEXT NOT NULL,
            "pathname"  TEXT NOT NULL,
            "target"    TEXT,
            "mode"      TEXT DEFAULT \'system\'
        )';
        $this->dbConnection->executeStatement($sql);
    }

    private function createIndices() {
        $this->createIndex_ida_frozen_file_node_idx();
        $this->createIndex_ida_frozen_file_pid_idx();
        $this->createIndex_ida_frozen_file_action_idx();
        $this->createIndex_ida_frozen_file_project_idx();
        $this->createIndex_ida_frozen_file_removed_idx();
        $this->createIndex_ida_action_pid_idx();
        $this->createIndex_ida_action_project_idx();
        $this->createIndex_ida_action_storage_idx();
        $this->createIndex_ida_action_completed_idx();
        $this->createIndex_ida_action_failed_idx();
        $this->createIndex_ida_action_cleared_idx();
        $this->createIndex_ida_data_change_init_idx();
        $this->createIndex_ida_data_change_last_idx();
        $this->createIndex_filecache_missing_checksums_idx();
        $this->createIndex_filecache_old_data_idx();
        $this->createIndex_filecache_extended_old_data_idx();
    }
    
    private function createIndex_ida_frozen_file_node_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_frozen_file_node_idx 
                ON ' . $this->dbPrefix . 'ida_frozen_file USING btree (node) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_frozen_file_pid_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_frozen_file_pid_idx 
                ON ' . $this->dbPrefix . 'ida_frozen_file USING btree (pid) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_frozen_file_action_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_frozen_file_action_idx 
                ON ' . $this->dbPrefix . 'ida_frozen_file USING btree (action) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_frozen_file_project_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_frozen_file_project_idx 
                ON ' . $this->dbPrefix . 'ida_frozen_file USING btree (project) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_frozen_file_removed_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_frozen_file_removed_idx 
                ON ' . $this->dbPrefix . 'ida_frozen_file USING btree (removed) 
                WITH (fillfactor = 80) 
                WHERE removed IS NULL';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_action_pid_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_action_pid_idx 
                ON ' . $this->dbPrefix . 'ida_action USING btree (pid) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_action_project_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_action_project_idx 
                ON ' . $this->dbPrefix . 'ida_action USING btree (project) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_action_storage_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_action_storage_idx 
                ON ' . $this->dbPrefix . 'ida_action USING btree (storage) 
                WITH (fillfactor = 80) 
                WHERE storage IS NULL';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_action_completed_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_action_completed_idx 
                ON ' . $this->dbPrefix . 'ida_action USING btree (completed) 
                WITH (fillfactor = 80) 
                WHERE completed IS NULL';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_action_failed_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_action_failed_idx 
                ON ' . $this->dbPrefix . 'ida_action USING btree (failed) 
                WITH (fillfactor = 80) 
                WHERE failed IS NULL';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_action_cleared_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_action_cleared_idx 
                ON ' . $this->dbPrefix . 'ida_action USING btree (cleared) 
                WITH (fillfactor = 80) 
                WHERE cleared IS NULL';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_data_change_init_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_data_change_init_idx 
                ON ' . $this->dbPrefix . 'ida_data_change USING btree (project, change, timestamp ASC) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_ida_data_change_last_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'ida_data_change_last_idx 
                ON ' . $this->dbPrefix . 'ida_data_change USING btree (project, timestamp DESC) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_filecache_missing_checksums_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'filecache_missing_checksums_idx 
                ON ' . $this->dbPrefix . 'filecache USING btree (storage, mimetype, checksum) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_filecache_old_data_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'filecache_old_data_idx 
                ON ' . $this->dbPrefix . 'filecache USING btree (storage, mimetype, path, mtime, fileid) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }
    
    private function createIndex_filecache_extended_old_data_idx() {
        $sql = 'CREATE INDEX IF NOT EXISTS ' . $this->dbPrefix . 'filecache_extended_old_data_idx 
                ON ' . $this->dbPrefix . 'filecache_extended USING btree (fileid, upload_time) 
                WITH (fillfactor = 80)';
        $this->dbConnection->executeQuery($sql);
    }

}
