<?php
/**
 * This file is part of the Fairdata IDA research data storage service.
 *
 * Copyright (C) 2023 Ministry of Education and Culture, Finland
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

namespace OCA\IDA\Db;

use OCA\IDA\Util\Access;
use OCA\IDA\Util\Constants;
use OCA\IDA\Util\Generate;
use OCA\IDA\Db\DataChange;
use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;
use Exception;

/**
 * Interact with the ida_frozen_file database table
 */
class DataChangeMapper extends QBMapper
{
    protected IDBConnection $dbConnection;
    protected LoggerInterface $logger;

    /**
     * Create the ida_frozen_file database mapper
     *
     * @param IDBConnection $dbConnection the database connection to use
     */
    public function __construct(IDBConnection $dbConnection, LoggerInterface $logger) {
        parent::__construct($dbConnection, 'ida_data_change', '\OCA\IDA\Db\DataChange');
        $this->dbConnection = $dbConnection;
        $this->logger = $logger;
    }

    /**
     * Retrieve the detauls of when the project was added to IDA, based on the oldest 'init' change, if defined.
     * Defaults to the IDA migration if no other 'init' change defined.
     */
    public function getInitializationDetails($project) {

        $this->logger->debug('getInitializationDetails: project=' . $project);

        $query = $this->dbConnection->getQueryBuilder();

        // SELECT * FROM *PREFIX*ida_data_change WHERE project = '<project>' AND change = 'init' ORDER BY timestamp ASC LIMIT 1
        $query->select('*')
              ->from('ida_data_change')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)))
              ->andWhere($query->expr()->eq('change', $query->createNamedParameter('init')))
              ->orderBy('timestamp', 'ASC')
              ->setMaxResults(1);
    
        $this->logger->debug('getInitializationDetails: query=' . Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();

        $this->logger->debug('getInitializationDetails: row=' . json_encode($row));

        if ($row) {
            $dataChangeEntity = DataChange::fromRow($row);
        }
        else {
            $dataChangeEntity = new DataChange();
            $dataChangeEntity->setTimestamp(Constants::IDA_MIGRATION);
            $dataChangeEntity->setProject($project);
            $dataChangeEntity->setUser('service');
            $dataChangeEntity->setChange('init');
            $dataChangeEntity->setPathname('/');
            $dataChangeEntity->setMode('system');
        }

        $this->logger->debug('getInitializationDetails: entity=' . json_encode($dataChangeEntity));

        return $dataChangeEntity;
    }

    /**
     * Retrieve the details of the last recorded 'add' change event for a particular relative pathname for a project, in staging, if any.
     */
    public function getLastAddChangeDetails($project, $pathname) {

        $this->logger->debug('getLastAddChangeDetails:' . ' project=' . $project . ' pathname=' . $pathname);
    
        $stagingPathname = '/' . $project . Constants::STAGING_FOLDER_SUFFIX . $pathname;
    
        $this->logger->debug('getLastAddChangeDetails: stagingPathname=' . $stagingPathname);
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_data_change WHERE project = '<project>' AND change = 'add' AND pathname = '<stagingPathname>' ORDER BY timestamp DESC LIMIT 1
        $query->select('*')
              ->from('ida_data_change')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)))
              ->andWhere($query->expr()->eq('change', $query->createNamedParameter('add')))
              ->andWhere($query->expr()->eq('pathname', $query->createNamedParameter($stagingPathname)))
              ->orderBy('timestamp', 'DESC')
              ->setMaxResults(1);
    
        $this->logger->debug('getLastAddChangeDetails: query=' . Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();

        $this->logger->debug('getLastAddChangeDetails: row=' . json_encode($row));

        if ($row) {
            $dataChangeEntity = DataChange::fromRow($row);
        }
        else {
            $dataChangeEntity = null;
        }
    
        $this->logger->debug('getLastAddChangeDetails: entity=' . json_encode($dataChangeEntity));

        return $dataChangeEntity;
    }

    /**
     * Retrieve the details of the last recorded data change event for a project, if any, else return details
     * from init corresponding to original legacy data migration event.
     */
    public function getLastDataChangeDetails($project, $user = null, $change = null, $mode = null) {

        $this->logger->debug(
            'getLastDataChangeDetails:'
            . ' project=' . $project
            . ' user=' . $user
            . ' change=' . $change
            . ' mode=' . $mode
        );
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_data_change WHERE project = '<project>' AND user = '<user>' AND change = '<change>' AND mode = '<mode>' ORDER BY timestamp DESC LIMIT 1
        $query->select('*')
              ->from('ida_data_change')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)));
        if ($user) {
            $query->andWhere($query->expr()->eq('user', $query->createNamedParameter($user)));
        }
        if ($change) {
            $query->andWhere($query->expr()->eq('change', $query->createNamedParameter($change)));
        }
        if ($mode) {
            $query->andWhere($query->expr()->eq('mode', $query->createNamedParameter($mode)));
        }

        $query->orderBy('timestamp', 'DESC')->setMaxResults(1);
    
        $this->logger->debug('getLastDataChangeDetails: query=' . Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();
    
        $this->logger->debug('getLastDataChangeDetails: row=' . json_encode($row));
    
        if ($row) {
            $dataChangeEntity = DataChange::fromRow($row);
        }
        else { 
            $dataChangeEntity = new DataChange();
            $dataChangeEntity->setTimestamp(Constants::IDA_MIGRATION);
            $dataChangeEntity->setProject($project);
            $dataChangeEntity->setUser('service');
            $dataChangeEntity->setChange('init');
            $dataChangeEntity->setPathname('/');
            $dataChangeEntity->setMode('system');
        }

        $this->logger->debug('getLastDataChangeDetails: entity=' . json_encode($dataChangeEntity));
    
        return $dataChangeEntity;
    }
    
    /**
     * Retrieve the details of the specified number of last recorded data change events for a project, if any,
     * else return details from original legacy data migration event; optionally limited to a particular
     * user and/or change.
     */
    public function getDataChangeDetails($project, $user = null, $change = null, $mode = null, $limit = null)
    {
        $this->logger->debug(
            'getDataChangeDetails:'
            . ' project=' . $project
            . ' user=' . $user
            . ' change=' . $change
            . ' mode=' . $mode
            . ' limit=' . $limit
        );
    
        if ($limit === null || trim($limit) === '') {
            $limit = 0;
        } else {
            $limit = (int)$limit;
        }
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_data_change WHERE project = '<project>' AND "user" = '<user>' AND change = '<change>' AND mode = '<mode>' ORDER BY timestamp DESC LIMIT <limit>
        $query->select('*')
              ->from('ida_data_change')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)));
    
        if ($user) {
            $query->andWhere($query->expr()->eq('user', $query->createNamedParameter($user)));
        }
    
        if ($change) {
            $query->andWhere($query->expr()->eq('change', $query->createNamedParameter($change)));
        }
    
        if ($mode) {
            $query->andWhere($query->expr()->eq('mode', $query->createNamedParameter($mode)));
        }
    
        $query->orderBy('timestamp', 'DESC');
    
        if ($limit > 0) {
            $query->setMaxResults($limit);
        }
    
        $this->logger->debug('getDataChangeDetails: query=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();

        $count = count($rows);
    
        $this->logger->debug('getDataChangeDetails: found=' . $count);
    
        if (($rows === null || $count === 0)
            && ($user === null || $user === 'service')
            && ($change === null || $change === 'init')
            && ($mode === null || $mode === 'system')
        ) {
            $dataChangeEntity = new DataChange();
            $dataChangeEntity->setTimestamp(Constants::IDA_MIGRATION);
            $dataChangeEntity->setProject($project);
            $dataChangeEntity->setUser('service');
            $dataChangeEntity->setChange('init');
            $dataChangeEntity->setPathname('/');
            $dataChangeEntity->setMode('system');
            $dataChangeEntities = array($dataChangeEntity);
        }
        else {
            $dataChangeEntities = array_map(fn($row) => DataChange::fromRow($row), $rows);
        }
    
        $this->logger->debug('getDataChangeDetails: dataChangeEntities=' . count($dataChangeEntities));
    
        return $dataChangeEntities;
    }
    

    /**
     * Record the details of a data change event for a project.
     */
    public function recordDataChangeDetails($project, $user, $change, $pathname, $target = null, $timestamp = null, $mode = null)
    {
        $this->logger->debug(
            'recordDataChangeDetails:'
            . ' project=' . $project
            . ' user=' . $user
            . ' change=' . $change
            . ' pathname=' . $pathname
            . ' target=' . $target
            . ' timestamp=' . $timestamp
            . ' mode=' . $mode
        );

        if ($project === null || $project === '') { throw new Exception('Project cannot be null'); }
        if ($user === null || $user === '') { throw new Exception('User cannot be null'); }
        if ($change === null || $change === '') { throw new Exception('Change cannot be null'); }
        if ($pathname === null || $pathname === '') { throw new Exception('Pathname cannot be null'); }

        if (! in_array($change, DataChange::CHANGES)) {
            throw new Exception('Invalid change specified.');
        }

        if (in_array($change, DataChange::TARGET_CHANGES) && $target === null) {
            throw new Exception('Target must be specified.');
        }

        // If admin or PSO user, record user as 'service', e.g. for a batch action, repair, etc.

        $user = trim($user);

        if ($user === null || $user === '' || $user === '--' || $user === 'admin' || strpos($user, Constants::PROJECT_USER_PREFIX) === 0) {
            $user = 'service';
        }

        if ($timestamp === null) {
            $timestamp = Generate::newTimestamp();
        }

        if ($mode === null || $mode === '') {
            $mode = 'api';
        }

        $dataChangeEntity = new DataChange();
        $dataChangeEntity->setTimestamp($timestamp);
        $dataChangeEntity->setProject($project);
        $dataChangeEntity->setUser($user);
        $dataChangeEntity->setChange($change);
        $dataChangeEntity->setPathname($pathname);
        $dataChangeEntity->setTarget($target);
        $dataChangeEntity->setMode($mode);

        $this->logger->debug('recordDataChangeDetails: entity=' . json_encode($dataChangeEntity));

        $this->insert($dataChangeEntity);

        return $dataChangeEntity;
    }

    /**
     * Delete all data change records in the database for the specified project, or for all projects if 'all' specfied
     */
    public function deleteAllDataChanges($project = null) {

        $query = $this->dbConnection->getQueryBuilder();
    
        // DELETE FROM *PREFIX*ida_data_change
        $query->delete('ida_data_change');
    
        if ($project != 'all') {
            // WHERE project = '<project>'
            $query->where($query->expr()->eq('project', $query->createNamedParameter($project)));
        }
    
        $this->logger->debug('deleteAllDataChanges: query=' . Generate::rawSQL($query));
    
        $query->executeStatement();
    }
    
}
