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

namespace OCA\IDA\Util;

use OCP\IUserSession;
use OCP\IGroupManager;
use OCP\IConfig;
use OCP\IDBConnection;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OC\DB\PgSqlConnection;
use Exception;

use function OCP\Log\logger;

/**
 * Class NotProjectUser
 *
 * Exception class to signal when the authenticated user does not belong to a specified project
 */
class NotProjectUser extends Exception
{
    public function __construct($message = null)
    {
        if ($message === null) {
            $this->message = 'Session user does not belong to the specified project.';
        } else {
            $this->message = $message;
        }
    }
}

/**
 * Various access management functions
 */
class Access
{
    /**
     * Return a string of comma separated names of all projects to which the user belongs.
     *
     * @return string
     */
    public static function getUserProjects()
    {

        $user = \OC::$server->get(IUserSession::class)->getUser();
        $userId = $user->getUID();

        if (strlen($userId) <= 0) {
            throw new Exception('No user found for session.');
        }

        // Fetch names of all project groups to which the user belongs
        $projects = implode(',', \OC::$server->get(IGroupManager::class)->getUserGroupIds($user));

        logger('ida')->debug('getUserProjects: projects=' . $projects);

        return $projects;
    }

    /**
     * Produced a clean, comma separated sequence of project names, with no superfluous whitespace.
     *
     * @param string $projects a comma separated sequence of project names
     *
     * @return string
     */
    public static function cleanProjectList($projects)
    {

        $cleanProjects = null;

        if ($projects) {
            $projects = trim($projects);
            $first = true;
            if ($projects) {
                foreach (explode(',', $projects) as $project) {
                    if ($first) {
                        $cleanProjects = trim($project);
                        $first = false;
                    } else {
                        $cleanProjects = $cleanProjects . ',' . trim($project);
                    }
                }
            }
        }

        return $cleanProjects;
    }

    /**
     * Throw exception if current user does not have rights to access the specified project (either is not a member
     * of the project or is not an admin).
     *
     * @param string $project the project name
     *
     * @throws NotProjectUser
     */
    public static function verifyIsAllowedProject($project)
    {

        if ($project === null || strlen($project) === 0) {
            throw new Exception('Missing project parameter.');
        }

        $userId = \OC::$server->get(IUserSession::class)->getUser()->getUID();

        logger('ida')->debug('verifyIsAllowedProject: userId=' . $userId . ' project=' . $project);

        if (strlen($userId) <= 0) {
            throw new Exception('No user found for session.');
        }

        // If user is PSO user for project, return (OK)
        if ($userId === Constants::PROJECT_USER_PREFIX . $project) {
            return;
        }

        // Throw exception if user is admin or does not belong to specified project group

        if (!\OC::$server->get(IGroupManager::class)->isInGroup($userId, $project)) {
            throw new NotProjectUser();
        }
    }

    /**
     * Returns true if the project lock file exists (e.g. due to an ongoing action), else returns false.
     *
     * @param string $project          the project name
     * @param string $lockFilePathname the full system pathname of the project lock file, if known
     *
     * @return bool
     */
    public static function projectIsLocked($project, $lockFilePathname = null)
    {
        if (!$project) {
            throw new Exception('Null project');
        }
        logger('ida')->debug('projectIsLocked: project=' . $project . ' lockFilePathname=' . $lockFilePathname);
        if ($lockFilePathname === null) {
            $lockFilePathname = self::buildLockFilePathname($project);
        }

        return (file_exists($lockFilePathname));
    }

    /**
     * Locks the specified project by creating the project lock file.
     * 
     * If the specified project is 'all', locks the entire service. If the service is already
     * locked, still returns true and the service remains locked.
     *
     * Returns true on success, else returns false if the project cannot be locked because either
     * the service is locked, or the project is already locked e.g. by another action. 
     * 
     * @param string $project the project name
     *
     * @return bool
     */
    public static function lockProject($project)
    {
        if (!$project) {
            throw new Exception('Null project');
        }
        logger('ida')->debug('lockProject: project=' . $project);
        if (self::projectIsLocked('all')) {
            if ($project !== 'all') {
                return false;
            }
            return true;
        }
        $lockFilePathname = self::buildLockFilePathname($project);
        if (self::projectIsLocked($project, $lockFilePathname)) {
            return false;
        }
        if (!touch($lockFilePathname)) {
            throw new Exception('Failed to create lock file for project ' . $project);
        }
        return true;
    }

    /**
     * Unlocks the specified project by removing the project lock file.
     *
     * Returns true on succeess, else throws exception if existing lock cannot be removed.
     *
     * @param string $project the project name
     *
     * @return bool
     */
    public static function unlockProject($project)
    {
        if (!$project) {
            throw new Exception('Null project');
        }
        logger('ida')->debug('unlockProject: project=' . $project);
        $lockFilePathname = self::buildLockFilePathname($project);
        if (self::projectIsLocked($project, $lockFilePathname)) {
            if (!unlink($lockFilePathname)) {
                throw new Exception('Failed to delete lock file for project ' . $project);
            }
        }
        return true;
    }

    /**
     * Builds and returns the full pathname of the lock file for the specified project.
     * 
     * If the specified project is 'all', builds and resturns system lock file pathname.
     *
     * @param string $project the project name
     *
     * @return string
     */
    protected static function buildLockFilePathname($project)
    {
        $dataRootPathname = \OC::$server->get(IConfig::class)->getSystemValueString('datadirectory', '/mnt/storage_vol01/ida');
        if ($project === 'all') {
            $lockFilePathname = $dataRootPathname . '/control/LOCK';
        } else {
            $lockFilePathname = $dataRootPathname . '/' . Constants::PROJECT_USER_PREFIX . $project . '/files/LOCK';
        }
        //logger('ida')->debug('buildLockFilePathname: lockFilePathname=' . $lockFilePathname);

        return ($lockFilePathname);
    }

    /**
     * Checks if the service is in offline mode.
     *
     * Returns true if service is offline, else returns false.
     *
     * @return bool
     */
    public static function serviceIsOffline()
    {
        $dataRootPathname = \OC::$server->get(IConfig::class)->getSystemValueString('datadirectory', '/mnt/storage_vol01/ida');
        $sentinelFile = $dataRootPathname . '/control/OFFLINE';
        if (file_exists($sentinelFile)) {
            logger('ida')->debug('serviceIsOffline: true');
            return true;
        }
        logger('ida')->debug('serviceIsOffline: false');
        return false;
    }

    /**
     * Puts the service into offline mode by creating the OFFLINE sentinel file.
     *
     * Returns true on success, else returns false. Always succeeds if the service is already in offline mode.
     *
     * @return bool
     */
    public static function setOfflineMode()
    {
        logger('ida')->debug('setOfflineMode');
        $dataRootPathname = \OC::$server->get(IConfig::class)->getSystemValueString('datadirectory', '/mnt/storage_vol01/ida');
        $sentinelFile = $dataRootPathname . '/control/OFFLINE';
        if (!file_exists($sentinelFile)) {
            if (!file_put_contents($sentinelFile, 'Service put into offline mode by explicit admin request')) {
                throw new Exception('Failed to create offline sentinel file');
            }
        }
        return true;
    }

    /**
     * Puts the service into online mode by removing any OFFLINE sentinel file.
     *
     * Returns true on success, else returns false. Always succeeds if the service is already in online mode.
     *
     * @return bool
     */
    public static function setOnlineMode()
    {
        logger('ida')->debug('setOnlineMode');
        $dataRootPathname = \OC::$server->get(IConfig::class)->getSystemValueString('datadirectory', '/mnt/storage_vol01/ida');
        $sentinelFile = $dataRootPathname . '/control/OFFLINE';
        if (file_exists($sentinelFile)) {
            if (!unlink($sentinelFile)) {
                throw new Exception('Failed to delete offline sentinel file');
            }
        }
        return true;
    }

    public static function getRawSQL(IQueryBuilder $queryBuilder): string
    {
        $sql = $queryBuilder->getSQL();
        $params = $queryBuilder->getParameters();
    
        // Get the actual table prefix from Nextcloud's configuration
        $config = \OC::$server->getConfig();
        $tablePrefix = $config->getSystemValue('dbtableprefix', '');
    
        // Convert *PREFIX* to actual table prefix
        $sql = str_replace('*PREFIX*', $tablePrefix, $sql);
    
        // Convert MySQL-style backticks (`) to PostgreSQL-compatible double quotes (")
        $sql = str_replace('`', '"', $sql);
    
        // Replace named parameters with actual values
        foreach ($params as $key => $value) {
            if (is_string($value)) {
                $quotedValue = "'" . str_replace("'", "''", $value) . "'";
            } elseif (is_null($value)) {
                $quotedValue = 'NULL';
            } elseif (is_bool($value)) {
                $quotedValue = $value ? 'TRUE' : 'FALSE';
            } elseif (is_int($value) || is_float($value)) {
                $quotedValue = (string) $value;
            } else {
                throw new \InvalidArgumentException("Unsupported parameter type: " . gettype($value));
            }
    
            // Ensure parameter keys are prefixed with ":" as used in Nextcloud's QueryBuilder
            $paramKey = is_string($key) ? ':' . ltrim($key, ':') : '?';
    
            // Replace placeholders with properly quoted values
            $sql = str_replace($paramKey, $quotedValue, $sql);
        }
    
        return $sql;
    }
    
}
