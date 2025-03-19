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
namespace OCA\IDA\Db;

use OCA\IDA\Util\Access;
use OCA\IDA\Util\Generate;
use OCP\AppFramework\Db\QBMapper;
use OCP\AppFramework\Db\Entity;
use OCP\IConfig;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;
use Exception;

/**
 * Interact with the ida_action database table
 */
class ActionMapper extends QBMapper
{
    protected IDBConnection $dbConnection;
    protected IConfig $config;
    protected LoggerInterface $logger;

    /**
     * Create the ida_action database mapper
     *
     * @param IDBConnection $dbConnection the database connection to use
     */
    public function __construct(IDBConnection $dbConnection, IConfig $config, LoggerInterface $logger) {
        parent::__construct($dbConnection, 'ida_action', '\OCA\IDA\Db\Action');
        $this->dbConnection = $dbConnection;
        $this->config = $config;
        $this->logger = $logger;
    }
    
    /**
     * Return true if any actions, possibly of a specified status, exist for one or more projects; else return false.
     *
     * pending:     there are ongoing background operations
     * completed:   action completed successfully
     * failed:      background operations have stopped due to some unrecoverable error
     * cleared:     failed action was cleared, possibly retried
     * incomplete:  action is either pending or failed (but not cleared); used to check for action conflicts
     * initiating:  action has not finished updating storage yet
     * suspend:     action is a suspend action
     *
     * @param string $status   one of 'pending', 'failed', 'completed', 'cleared', 'incomplete', 'initiating', or 'suspend'
     * @param string $projects one or more comma separated project names, with no whitespace
     *
     * @return bool
     */
    public function hasActions($status = null, $projects = null) {

        $this->logger->debug('hasActions: status=' . $status . ' projects=' . $projects);

        $query = $this->dbConnection->getQueryBuilder();

        // SELECT * FROM *PREFIX*ida_action
        $query->select('*')->from('ida_action');

        if ($status) {
            switch ($status) {
                case 'pending':
                    // WHERE cleared IS NULL AND completed IS NULL AND failed IS NULL AND action != 'suspend';
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->isNull('failed'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'completed':
                    // WHERE cleared IS NULL AND completed IS NOT NULL';
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNotNull('completed'));
                    break;
                case 'failed':
                    // WHERE cleared IS NULL AND failed IS NOT NULL';
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNotNull('failed'));
                    break;
                case 'cleared':
                    // WHERE cleared IS NOT NULL';
                    $query->where($query->expr()->isNotNull('cleared'));
                    break;
                case 'incomplete':
                    // WHERE cleared IS NULL AND completed IS NULL AND action != 'suspend';
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'initiating':
                    // WHERE cleared IS NULL AND storage IS NULL AND action != 'suspend';
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('storage'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'suspend':
                    // WHERE cleared IS NULL AND completed IS NULL AND action = 'suspend';
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->eq('action', $query->createNamedParameter('suspend')));
                    break;
                default:
                    throw new \InvalidArgumentException("Invalid action status: \"$status\"");
            }
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }   

        // LIMIT 1
        $query->setMaxResults(1);

        $this->logger->debug('hasActions: query=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();
    
        $count = count($rows);

        $this->logger->debug('hasActions: found=' . $count);

        return ($count > 0);
    }

    /**
     * Return true if any pending suspend action exists for one or more projects, or if all projects are suspended via the SUSPEND sentinel file; else return false.
     *
     * @param string $projects one or more comma separated project names, with no whitespace
     *
     * @return bool
     */
    public function isSuspended($projects = null): bool {

        $sentinelFilePathname = $this->config->getSystemValue('datadirectory', '/mnt/storage_vol01/ida') . '/control/SUSPENDED';
    
        // If the sentinel file exists, the project is suspended
        if (file_exists($sentinelFilePathname)) {
            return true;
        }
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_action WHERE action = 'suspend' AND cleared IS NULL AND completed IS NULL AND failed IS NULL
        $query->select('*')
              ->from('ida_action')
              ->where($query->expr()->eq('action', $query->createNamedParameter('suspend')))
              ->andWhere($query->expr()->isNull('cleared'))
              ->andWhere($query->expr()->isNull('completed'))
              ->andWhere($query->expr()->isNull('failed'));
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }   

        // LIMIT 1
        $query->setMaxResults(1);
    
        // Log the resultant SQL query for debugging
        $this->logger->debug('isSuspended: query=' . Generate::rawSQL($query));
    
        // Execute the query and fetch results
        $rows = $query->executeQuery()->fetchAll();
    
        $count = count($rows);

        $this->logger->debug('isSuspended: found=' . $count);

        return ($count > 0);
    }

    /**
     * Return all actions, optionally constrained by status and to one or more projects.
     *
     * pending:     there are ongoing background operations
     * completed:   action completed successfully
     * failed:      background operations have stopped due to some unrecoverable error
     * cleared:     failed action was cleared, possibly retried
     * incomplete:  action is either pending or failed (but not cleared); used to check for action conflicts
     * initiating:  action has not finished updating storage yet
     * suspend:     action is a suspend action
     *
     * @param string $status   one of 'pending', 'failed', 'completed', 'cleared', 'incomplete', 'initiating', or 'suspend'
     * @param string $projects one or more comma separated project names, with no whitespace
     *
     * @return Entity[]
     */
    public function findActions($status = null, $projects = null) {
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_action
        $query->select('*')->from('ida_action');
    
        if ($status) {

            switch ($status) {
                case 'pending':
                    // WHERE cleared IS NULL AND completed IS NULL AND failed IS NULL AND action != 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->isNull('failed'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'completed':
                    // WHERE cleared IS NULL AND completed IS NOT NULL
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNotNull('completed'));
                    break;
                case 'failed':
                    // WHERE cleared IS NULL AND failed IS NOT NULL
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNotNull('failed'));
                    break;
                case 'cleared':
                    // WHERE cleared IS NOT NULL
                    $query->where($query->expr()->isNotNull('cleared'));
                    break;
                case 'incomplete':
                    // WHERE cleared IS NULL AND completed IS NULL AND action != 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'initiating':
                    // WHERE cleared IS NULL AND storage IS NULL AND action != 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('storage'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'suspend':
                    // WHERE cleared IS NULL AND completed IS NULL AND action = 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->eq('action', $query->createNamedParameter('suspend')));
                    break;
                default:
                    throw new \Exception('Invalid action status: "' . $status . '"');
                    break;
            }
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }
    
        if ($status === 'completed') {
            // ORDER BY completed DESC
            $query->orderBy('completed', 'DESC');
        }
        elseif ($status === 'failed') {
            // ORDER BY failed DESC
            $query->orderBy('failed', 'DESC');
        }
        elseif ($status === 'cleared') {
            // ORDER BY cleared DESC
            $query->orderBy('cleared', 'DESC');
        }
        else {
            // ORDER BY initiated DESC
            $query->orderBy('initiated', 'DESC');
        }
    
        $this->logger->debug('findActions: query=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();

        $this->logger->debug('findActions: found=' . count($rows));
    
        return array_map(fn($row) => Action::fromRow($row), $rows);
    }

    /**
     * Return count of all actions, optionally constrained by status and to one or more projects.
     *
     * pending:     there are ongoing background operations
     * completed:   action completed successfully
     * failed:      background operations have stopped due to some unrecoverable error
     * cleared:     failed action was cleared, possibly retried
     * incomplete:  action is either pending or failed (but not cleared); used to check for action conflicts
     * initiating:  action has not finished updating storage yet
     * suspend:     action is a suspend action
     *
     * @param string $status   one of 'pending', 'failed', 'completed', 'cleared', 'incomplete', 'initiating', or 'suspend'
     * @param string $projects one or more comma separated project names, with no whitespace
     *
     * @return int
     */
    public function countActions($status = null, $projects = null) {

        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT COUNT(*) FROM *PREFIX*ida_action
        $query->select($query->createFunction('COUNT(*)'))->from('ida_action');
    
        if ($status) {
            switch ($status) {
                case 'pending':
                    // WHERE cleared IS NULL AND completed IS NULL AND failed IS NULL AND action != 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->isNull('failed'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'completed':
                    // WHERE cleared IS NULL AND completed IS NOT NULL
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNotNull('completed'));
                    break;
                case 'failed':
                    // WHERE cleared IS NULL AND failed IS NOT NULL
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNotNull('failed'));
                    break;
                case 'cleared':
                    // WHERE cleared IS NOT NULL
                    $query->where($query->expr()->isNotNull('cleared'));
                    break;
                case 'incomplete':
                    // WHERE cleared IS NULL AND completed IS NULL AND action != 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'initiating':
                    // WHERE cleared IS NULL AND storage IS NULL AND action != 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('storage'))
                          ->andWhere($query->expr()->neq('action', $query->createNamedParameter('suspend')));
                    break;
                case 'suspend':
                    // WHERE cleared IS NULL AND completed IS NULL AND action = 'suspend'
                    $query->where($query->expr()->isNull('cleared'))
                          ->andWhere($query->expr()->isNull('completed'))
                          ->andWhere($query->expr()->eq('action', $query->createNamedParameter('suspend')));
                    break;
                default:
                    throw new \Exception('Invalid action status: "' . $status . '"');
                    break;
            }
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }   
   
        $this->logger->debug('countActions: query=' . Generate::rawSQL($query));
    
        $count = (int) $query->executeQuery()->fetchOne();

        $this->logger->debug('countActions: found=' . $count);
    
        return $count;
    }

    /**
     * Return an action based on a PID, or null if no action has the specified PID, optionally limited to one or more projects
     *
     * @param string $pid      the PID of the action
     * @param string $projects one or more comma separated project names, with no whitespace
     *
     * @return Entity
     */
    public function findAction($pid, $projects = null) {

        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_action WHERE pid = '<pid>'
        $query->select('*')
              ->from('ida_action')
              ->where($query->expr()->eq('pid', $query->createNamedParameter($pid)));
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }   
        
        $this->logger->debug('findAction: query=' . Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();

        $this->logger->debug('findAction: row=' . json_encode($row));

        if ($row) {
            $actionEntity = Action::fromRow($row);
        }
        else {
            $actionEntity = null;
        }

        $this->logger->debug('findAction: action=' . json_encode($actionEntity));

        return $actionEntity;
    }

    /**
     * Clear a failed action
     *
     * @param string $pid the PID of the action
     *
     * @return Entity
     * @throws Exception
     */
    public function clearAction($pid) {
        
        $actionEntity = $this->findAction($pid);
        
        if ($actionEntity) {
            if ($actionEntity->getFailed() === null) {
                throw new Exception('The action with PID "' . $pid . '" is not failed. Only failed actions may be cleared.');
            }
            $actionEntity->setCleared(Generate::newTimestamp());
        }
        else {
            throw new Exception('No action found with specified PID "' . $pid . '"');
        }
        
        return $this->update($actionEntity);
    }
    
    /**
     * Clear all actions, by default limited to failed actions, optionally restricted to one or more projects
     *
     * @param string $projects one or more comma separated project names, with no whitespace
     *
     * @return Entity[]
     */
    public function clearActions($status = 'failed', $projects = null) {
        
        $actionEntities = $this->findActions($status, $projects);
        
        foreach ($actionEntities as $actionEntity) {
            $this->clearAction($actionEntity->getPid());
        }
        
        return $actionEntities;
    }
    
    /**
     * Delete a specific action record from the database
     * 
     * @param string $pid the PID of the action
     */
    public function deleteAction($pid) {

        $query = $this->dbConnection->getQueryBuilder();
    
        // DELETE FROM *PREFIX*ida_action WHERE pid = '<pid>'
        $query->delete('ida_action')
              ->where($query->expr()->eq('pid', $query->createNamedParameter($pid)));
    
        $this->logger->debug('deleteAction: query=' . Generate::rawSQL($query));
    
        $query->executeStatement();
    }
        
    /**
     * Delete all action records in the database for the specified project, or for all projects if 'all' specfied
     * 
     * @param string $project the project name, or 'all'
     */
    public function deleteAllActions($project = null) {

        $query = $this->dbConnection->getQueryBuilder();
    
        // DELETE FROM *PREFIX*ida_action
        $query->delete('ida_action');
    
        if ($project !== 'all') {
            // WHERE project = '<project>'
            $query->where($query->expr()->eq('project', $query->createNamedParameter($project)));
        }
    
        $this->logger->debug('deleteAllActions: query=' . Generate::rawSQL($query));
    
        $query->executeStatement();
    }
    
}

