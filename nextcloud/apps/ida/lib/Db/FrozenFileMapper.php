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
use OCA\IDA\Db\FrozenFile;
use OCA\IDA\Util\Generate;
use OCP\AppFramework\Db\QBMapper;
use OCP\AppFramework\Db\Entity;
use OCP\IDBConnection;
use Psr\Log\LoggerInterface;

/**
 * Interact with the ida_frozen_file database table
 */
class FrozenFileMapper extends QBMapper
{
    protected IDBConnection $dbConnection;
    protected LoggerInterface $logger;

    /**
     * Create the ida_frozen_file database mapper
     *
     * @param IDBConnection $dbConnection the database connection to use
     */
    public function __construct(IDBConnection $dbConnection, LoggerInterface $logger) {
        parent::__construct($dbConnection, 'ida_frozen_file', '\OCA\IDA\Db\FrozenFile');
        $this->dbConnection = $dbConnection;
        $this->logger = $logger;
    }

    /**
     * Retrieve all frozen file records associated with the specified action, based on the provided action PID,
     * optionally restricted to one or more projects.
     *
     * @param string $pid      the PID of an action
     * @param string $projects one or more comma separated project names, with no whitespace
     * @param int    $limit    limit total to optionally specified maximum
     *
     * @return FrozenFile[]
     */
    public function findActionFiles($pid = null, $projects = null, $limit = null) {

        $this->logger->debug(
            'findActionFiles:' 
            . ' pid=' . $pid
            . ' projects=' . $projects
            . ' limit=' . $limit
        );
    
        $query = $this->dbConnection->getQueryBuilder();
        $where = false;
        
        // SELECT * FROM *PREFIX*ida_frozen_file
        $query->select('*')->from('ida_frozen_file');
    
        if ($pid) {
            // WHERE action = '<pid>'
            $query->where($query->expr()->eq('action', $query->createNamedParameter($pid)));
            $where = true;
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                if ($where) {
                    // AND project IN ('project1', 'project2', ...)
                    $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
                }
                else {
                // WHERE project IN ('project1', 'project2', ...)
                    $query->where($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
                    $where = true;
                }
            }
        }
    
        // ORDER BY pathname ASC
        $query->orderBy('pathname', 'ASC');
    
        // If limit specified, restrict query to limit
        if ($limit && is_integer($limit)) {
            $query->setMaxResults($limit);
        }
    
        $this->logger->debug('findActionFiles: query=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();

        $count = count($rows);

        $this->logger->debug('findActionFiles: found=' . $count);

        return array_map(fn($row) => FrozenFile::fromRow($row), $rows);
    }
    
    /**
     * Retrieve the PIDs of all frozen file records associated with the specified project.
     *
     * @param string  $project          a project name
     * @param boolean $includeInactive  include removed and cleared file records
     *
     * @return string[]
     */
    public function getFrozenFilePids($project, $includeInactive = false) {

        $this->logger->debug(
            'getFrozenFilePids:' 
            . ' project=' . $project
            . '$includeInactive=' . $includeInactive
        );
    
        $frozenFilePids = array();
    
        $query = $this->dbConnection->getQueryBuilder();
        
        // SELECT * FROM *PREFIX*ida_frozen_file WHERE project = <project>
        $query->select('*')
              ->from('ida_frozen_file')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)));
    
        if ($includeInactive === false) {
            // AND removed IS NULL AND cleared IS NULL
            $query->andWhere($query->expr()->isNull('removed'))
                  ->andWhere($query->expr()->isNull('cleared'));
        }
    
        $this->logger->debug('getFrozenFilePids: query=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();
    
        foreach ($rows as $row) {
            $frozenFilePids[] = $row['pid'];
        }
    
        return $frozenFilePids;
    }
    

    /**
     * Count the total file records associated with the specified action, based on the provided action PID,
     * optionally restricted to one or more projects.
     *
     * @param string  $pid             the PID of an action
     * @param string  $projects        one or more comma separated project names, with no whitespace
     * @param boolean $includeInactive include removed and cleared file records
     *
     * @return FrozenFile[]
     */
    public function countActionFiles($pid = null, $projects = null, $includeInactive = true) {

        $this->logger->debug(
            'countActionFiles:' 
            . ' pid=' . $pid
            . ' projects=' . $projects
            . '$includeInactive=' . $includeInactive
        );
    
        $query = $this->dbConnection->getQueryBuilder();
        $where = false;

        // SELECT COUNT(*) FROM *PREFIX*ida_frozen_file
        $query->select('COUNT(*)')->from('ida_frozen_file');
    
        if ($pid) {
            // WHERE action = <pid>
            $query->where($query->expr()->eq('pid', $query->createNamedParameter($pid)));
            $where = true;
        }
    
        if ($includeInactive === false) {
            if ($where) {
                // AND removed IS NULL AND cleared IS NULL
                $query->andWhere($query->expr()->isNull('removed'))
                      ->andWhere($query->expr()->isNull('cleared'));
            }
            else {
                // WHERE removed IS NULL AND cleared IS NULL
                $query->where($query->expr()->isNull('removed'))
                      ->andWhere($query->expr()->isNull('cleared'));
                $where = true;
            }
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                $values = array_map(fn($p) => $query->createNamedParameter($p), $projectNames);
                if ($where) {
                    // AND project IN ('project1', 'project2', ...)
                    $query->andWhere($query->expr()->in('project', $values));
                }
                else {
                    // WHERE project IN ('project1', 'project2', ...)
                    $query->andWhere($query->expr()->in('project', $values));
                }
            }
        }
    
        $this->logger->debug('countActionFiles: sql=' . Generate::rawSQL($query));
    
        $count = (int) $query->executeQuery()->fetchOne();

        $this->logger->debug('countActionFiles: count=' . $count);
    
        return $count;
    }

    /**
     * Return the most recently created frozen file record with the specified PID, or null if not
     * found, optionally limited to one or more projects.
     *
     * @param string  $pid             the PID of the frozen file
     * @param string  $projects        one or more comma separated project names, with no whitespace
     * @param boolean $includeInactive include removed and cleared file records
     *
     * @return Entity
     */
    public function findFile($pid, $projects = null, $includeInactive = false)
    {
        $this->logger->debug(
            'findFile:' 
            . ' pid=' . $pid
            . ' projects=' . $projects
            . '$includeInactive=' . $includeInactive
        );
    
        $query = $this->dbConnection->getQueryBuilder();

        // SELECT * FROM *PREFIX*ida_frozen_file WHERE pid = <pid>
        $query->select('*')
              ->from('ida_frozen_file')
              ->where($query->expr()->eq('pid', $query->createNamedParameter($pid)));
    
        if ($includeInactive === false) {
            // AND removed IS NULL AND cleared IS NULL
            $query->andWhere($query->expr()->isNull('removed'))
                  ->andWhere($query->expr()->isNull('cleared'));
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }       

        // ORDER BY id DESC LIMIT 1
        $query->orderBy('id', 'DESC')->setMaxResults(1);
    
        $this->logger->debug('findFile: sql=' . Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();

        $this->logger->debug('findFile: row=' . json_encode($row));

        if ($row) {
            return FrozenFile::fromRow($row);
        }

        return null;
    }
    
    /**
     * Return the most recently created active frozen file record with the specified Nextcloud node ID, or null if no
     * file record has the specified node ID, optionally limited to one or more projects.
     *
     * @param integer $node            the Nextcloud node ID of the frozen file
     * @param string  $projects        one or more comma separated project names, with no whitespace
     * @param boolean $includeInactive include removed and cleared file records
     *
     * @return Entity
     */
    public function findByNextcloudNodeId($node, $projects = null, $includeInactive = false) {

        $this->logger->debug(
            'findByNextcloudNodeId:' 
            . ' node=' .  $node
            . ' projects=' . $projects
            . ' includeInactive=' . $includeInactive
        );
    
        $query = $this->dbConnection->getQueryBuilder();

        // SELECT * FROM *PREFIX*ida_frozen_file WHERE node = <node>
        $query->select('*')
              ->from('ida_frozen_file')
              ->where($query->expr()->eq('node', $query->createNamedParameter($node)));

        if ($includeInactive === false) {
            // AND removed IS NULL AND cleared IS NULL
            $query->andWhere($query->expr()->isNull('removed'))
                  ->andWhere($query->expr()->isNull('cleared'));
        }

        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }

        // ORDER BY id DESC LIMIT 1
        $query->orderBy('id', 'DESC')->setMaxResults(1);
    
        $this->logger->debug('findByNextcloudNodeId: sql=' .  Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();

        $this->logger->debug('findFile: row=' . json_encode($row));

        if ($row) {
            return FrozenFile::fromRow($row);
        }

        return null;
    }

    /**
     * Retrieve the most recently created active frozen file record with the specified project and pathname, or null if
     * not found, optionally restricted to one or more projects.
     *
     * @param string  $project         the project to which the file belongs
     * @param string  $pathname        the full relative pathname of the file to retrieve, rooted in the project's frozen directory
     * @param string  $projects        one or more comma separated project names, with no whitespace
     * @param boolean $includeInactive include removed and cleared file records
     *
     * @return Entity
     */
    public function findByProjectPathname($project, $pathname, $projects = null, $includeInactive = false) {

        $this->logger->debug(
            'findByprojectPathname:' 
            . ' project=' . $project
            . ' pathname=' .  $pathname
            . ' projects=' .  $projects
            . ' includeInactive=' . $includeInactive
        );
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_frozen_file WHERE project = <project> AND pathname = <pathname>
        $query->select('*')
              ->from('ida_frozen_file')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)))
              ->andWhere($query->expr()->eq('pathname', $query->createNamedParameter($pathname)));
    
        if ($includeInactive === false) {
            // AND removed IS NULL AND cleared IS NULL
            $query->andWhere($query->expr()->isNull('removed'))
                  ->andWhere($query->expr()->isNull('cleared'));
        }
    
        if ($projects) {
            $projectNames = array_map(fn($p) => $p, explode(',', Access::cleanProjectList($projects)));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in('project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }
    
        // ORDER BY id DESC LIMIT 1
        $query->orderBy('id', 'DESC')->setMaxResults(1);
    
        $this->logger->debug('findByProjectPathname: sql=' . Generate::rawSQL($query));
    
        $row = $query->executeQuery()->fetch();

        $this->logger->debug('findFile: row=' . json_encode($row));

        if ($row) {
            return FrozenFile::fromRow($row);
        }
    
        return null;
    }
    
    /**
     * Retrieve all frozen file records associated with the specified project where the
     * frozen file pathname is included in the specified list of pathnames.
     *
     * @param string  $project         the project name
     * @param array   $pathnames       the pathnames to include
     * @param boolean $includeInactive include removed and cleared file records
     *
     * @return FrozenFile[]
     */
    public function findFrozenFilesByPathnames($project, $pathnames, $includeInactive = false)
    {
        $this->logger->debug(
            'findFrozenFilesByPathnames:' 
            . ' project=' . $project
            . ' pathnames=' .  count($pathnames)
            . ' includeInactive=' . $includeInactive
        );
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_frozen_file WHERE project = <project>
        $query->select('*')
              ->from('ida_frozen_file')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)));
    
        // AND pathname IN ('pathname1', 'pathname2', ...)
        $pathnamesEscaped = array_map(fn($pathname) => $pathname, $pathnames);
        $query->andWhere($query->expr()->in('pathname', array_map(fn($p) => $query->createNamedParameter($p), $pathnamesEscaped)));
    
        if ($includeInactive === false) {
            // AND removed IS NULL AND cleared IS NULL
            $query->andWhere($query->expr()->isNull('removed'))
                  ->andWhere($query->expr()->isNull('cleared'));
        }
    
        $this->logger->debug('findFrozenFilesByPathnames: sql=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();

        $count = count($rows);

        $this->logger->debug('findFrozenFilesByPathnames: found=' . $count);

        return array_map(fn($row) => FrozenFile::fromRow($row), $rows);
    }

    /**
     * Retrieve all frozen file records associated with the specified project.
     *
     * @param string  $project         the project name
     * @param boolean $includeInactive include removed and cleared file records
     *
     * @return FrozenFile[]
     */
    public function findFrozenFiles($project, $includeInactive = false)
    {
        $this->logger->debug(
            'findFrozenFiles:' 
            . ' project=' . $project
            . ' includeInactive=' . $includeInactive
        );
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // SELECT * FROM *PREFIX*ida_frozen_file WHERE project = <project>
        $query->select('*')
              ->from('ida_frozen_file')
              ->where($query->expr()->eq('project', $query->createNamedParameter($project)));
    
        if ($includeInactive === false) {
            // AND removed IS NULL AND cleared IS NULL
            $query->andWhere($query->expr()->isNull('removed'))
                  ->andWhere($query->expr()->isNull('cleared'));
        }
    
        $this->logger->debug('findFrozenFiles: sql=' . Generate::rawSQL($query));
    
        $rows = $query->executeQuery()->fetchAll();

        $count = count($rows);

        $this->logger->debug('findFrozenFiles: found=' . $count);

        return array_map(fn($row) => FrozenFile::fromRow($row), $rows);
    }
    
    /**
     * Delete all file records associated with the specified action, based on the provided action PID,
     * optionally restricted to one or more projects..
     *
     * This function is only used when rolling back / cleaning up if something goes amiss while registering
     * all files associated with an action, and should not be used otherwise.
     *
     * @param string $pid      the PID of an action
     * @param string $projects one or more comma separated project names, with no whitespace
     */
    public function deleteActionFiles($pid, $projects = null)
    {
        $this->logger->debug(
            'deleteActionFiles:' 
            . ' pid=' . $pid
            . ' projects=' . $projects
        );
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // DELETE FROM *PREFIX*ida_frozen_file WHERE action = <pid>
        $query->delete('ida_frozen_file')
              ->where($query->expr()->eq('action', $query->createNamedParameter($pid)));
    
        if ($projects) {
            $projects = Access::cleanProjectList($projects);
            $projectNames = array_map(fn($p) => $p, explode(',', $projects));
            if (!empty($projectNames)) {
                // AND project IN ('project1', 'project2', ...)
                $query->andWhere($query->expr()->in( 'project', array_map(fn($p) => $query->createNamedParameter($p), $projectNames)));
            }
        }
    
        $this->logger->debug('deleteActionFiles: sql=' . Generate::rawSQL($query));
    
        $query->executeStatement();
    }
    
    /**
     * Delete all frozen file records with the specified PID from the database
     */
    public function deleteFile($pid)
    {
        $this->logger->debug('deleteFile: pid=' . $pid);
    
        $query = $this->dbConnection->getQueryBuilder();
    
        // DELETE FROM *PREFIX*ida_frozen_file WHERE pid = <pid>
        $query->delete('ida_frozen_file')
              ->where($query->expr()->eq('pid', $query->createNamedParameter($pid)));
    
        $this->logger->debug('deleteFile: sql=' . Generate::rawSQL($query));
    
        $query->executeStatement();
    }
    
    /**
     * Delete all file records in the database for the specified project, or for all projects if 'all' specified
     */
    public function deleteAllFiles($project = null)
    {
        $this->logger->debug('deleteAllFiles: project=' . $project);

        if ($project) {

            $query = $this->dbConnection->getQueryBuilder();
        
            // DELETE FROM *PREFIX*ida_frozen_file
            $query->delete('ida_frozen_file');
    
            if ($project !== 'all') {
                // WHERE project = <project>
                $query->where($query->expr()->eq('project', $query->createNamedParameter($project)));
            }
    
            $this->logger->debug('deleteAllFiles: sql=' . Generate::rawSQL($query));
    
            $query->executeStatement();
        }
    }
}

