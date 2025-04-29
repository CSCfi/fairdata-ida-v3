<?php
/**
 * This file is part of the IDA research data storage service
 *
 * Copyright (C) 2025 Ministry of Education and Culture, Finland
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
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * @author    CSC - IT Center for Science Ltd., Espoo Finland <servicedesk@csc.fi>
 * @license   GNU Affero General Public License, version 3
 * @link      https://www.fairdata.fi/en/ida
 */

namespace OCA\IDA\Util;

use Exception;
use OCA\IDA\Util\Constants;
use OCA\IDA\Util\Access;
use OCP\IDBConnection;
use OCP\DB\QueryBuilder\IQueryBuilder;
use OCP\Util;
use OC\Files\FileInfo;
use OC\Files\View;

use function OCP\Log\logger;

/**
 * Retrieve all essential details from the database to populate FileInfo instances efficiently
 */
class FileDetailsHelper
{
    private IDBConnection $db;
    private View $fsView;

    public function __construct($fsView) {
        $this->db = \OC::$server->getDatabaseConnection();
        $this->fsView = $fsView;
    }

    /**
     * Fetch all files for a user, optionally filtering by path prefix and limit.
     * 
     * @param string $project      the project to which the files should belong
     * @param string $fullPathname the full pathname of a node starting from the frozen or staging area root folder
     * @param int    $limit        the maximum total number of files allowed (zero = no limit)
     * 
     * @return array ['count' => (int)total, 'files' => FileInfo[]]
     */
    public function getFileDetails(string $project, string $fullPathname, int $limit): array {

        logger('ida')->debug('getFileDetails:' . 'project=' . $project . ' fullPathname=' . $fullPathname . ' limit=' . $limit);

        $psoUserId = 'home::' . Constants::PROJECT_USER_PREFIX . $project;

        logger('ida')->debug('getFileDetails: psoUserId=' . $psoUserId);

        // Get user's storage numeric ID

        try {
            $qb = $this->db->getQueryBuilder();

            $qb->select('numeric_id')
               ->from('storages')
               ->where($qb->expr()->eq('id', $qb->createNamedParameter($psoUserId)));

            //logger('ida')->debug('getFileDetails: sql=' . Access::getRawSQL($qb));

            $storageId = $qb->executeQuery()->fetchOne(); // NC30

        } catch (Exception $e) {
            logger('ida')->warning('getFileDetails: Error retrieving storage id for user ' . $psoUserId . ': ' . $e);
            $storageId = null;
        }

        logger('ida')->debug('getFileDetails: storageId=' . $storageId);

        // If project user doesn't exist, return empty results rather than throw exception

        if (is_null($storageId) || !isset($storageId) || !is_int($storageId)) {
            return ['count' => 0, 'files' => []];
        }

        // Query filecache to check if pathname corresponds to single file

        $qb = $this->db->getQueryBuilder();

        $qb->select('path')
            ->from('filecache')
            ->where($qb->expr()->eq('storage', $qb->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)))
            ->andWhere($qb->expr()->neq('mimetype', $qb->createNamedParameter(2, IQueryBuilder::PARAM_INT))) // 2 = folder, i.e. not a folder, i.e. a file
            ->andWhere($qb->expr()->eq('path', $qb->createNamedParameter('files' . $fullPathname)))
            ->orderBy('fileid', 'DESC')
            ->setMaxResults(1);

        //logger('ida')->debug('getFileDetails: sql=' . Access::getRawSQL($qb));

        $cache_files = $qb->execute()->fetchAll();

        if (empty($cache_files)) {

            // Since no file matches pathname, assume pathname corresponds to folder, verify folder at that pathname exists

            $qb = $this->db->getQueryBuilder();

            $qb->select('path')
                ->from('filecache')
                ->where($qb->expr()->eq('storage', $qb->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)))
                ->andWhere($qb->expr()->eq('mimetype', $qb->createNamedParameter(2, IQueryBuilder::PARAM_INT))) // 2 = folder, i.e. a folder
                ->andWhere($qb->expr()->eq('path', $qb->createNamedParameter('files' . $fullPathname)))
                ->orderBy('fileid', 'DESC')
                ->setMaxResults(1);

            //logger('ida')->debug('getFileDetails: sql=' . Access::getRawSQL($qb));

            $cache_files = $qb->execute()->fetchAll();

            if (!empty($cache_files)) {

                // If pathname matches folder, query filecache for all matching file paths, excluding folders, that
                // have the pathname as a prefix (exist within the folder as a descendant)

                $qb = $this->db->getQueryBuilder();
 
                $qb->select('path')
                    ->from('filecache')
                    ->where($qb->expr()->eq('storage', $qb->createNamedParameter($storageId, IQueryBuilder::PARAM_INT)))
                    ->andWhere($qb->expr()->neq('mimetype', $qb->createNamedParameter(2, IQueryBuilder::PARAM_INT))) // 2 = folder, i.e. not a folder, i.e. a file
                    ->andWhere($qb->expr()->like('path', $qb->createNamedParameter('files' . $fullPathname . '/%')))
                    ->orderBy('path', 'ASC');
  
                // Apply limit if defined (we add 1 to the limit to be able to check if we went over)
   
                if ($limit > 0) {
                    $qb->setMaxResults($limit + 1);
                }
    
                //logger('ida')->debug('getFileDetails: sql=' . Access::getRawSQL($qb));

                $cache_files = $qb->execute()->fetchAll();
            }
        }
    
        $files = [];
        $i = 0;

        foreach ($cache_files as $cache_file) {
            try {
                $path = $cache_file['path'];
                $fullPathname = substr($path, 5); // remove prefix substring 'files', starts then with frozen or staging folder
                $fileInfo = $this->fsView->getFileInfo($fullPathname);

                if ($fileInfo) {
                    $files[] = $fileInfo;
                    logger('ida')->debug('getFileDetails: (' . $i . ') fullPathname=' . $fullPathname);
                    $i++;
                }
            } catch (Exception $e) { 
                // Ignore any failures to construct FileInfo instances, which may be due to issues being repaired
                // based on the details returned by this function
                logger('ida')->debug('getFileDetails: Error retrieving file info for ' . $fullPathname . ': ' . $e);
            }
        }

        $count = count($files);

        logger('ida')->debug('getFileDetails: count=' . $count);

        return [ 'count' => $count, 'files' => $files ];
    }

    /**
     * Fetch the latest pathname, timestamp pairs from the data changes table for the specified
     * project and scope, corresponding to when files were added to staging.
     * 
     * @param string $project  the project to which the files should belong
     * @param string $scope    the scope that pathnames should begin with
     * 
     * @return array [ pathname => timestamp, ... ]
     */
    public function getDataChangeLastAddTimestamps(string $project, string $scope): array {

        logger('ida')->debug('getDataChangeLastAddTimestamps:' . 'project=' . $project . ' scope=' . $scope);

        // Get QueryBuilder instance from Nextcloud's DB connection
        $qb = $this->db->getQueryBuilder();

        // Define the pathname prefix
        $stagingPathnamePrefix = '/' . $project . Constants::STAGING_FOLDER_SUFFIX . $scope . '%';

        // Build the query
        $qb->select([
                'ida.pathname',
                'ida.timestamp'
            ])
            ->from('ida_data_change', 'ida')
            ->where($qb->expr()->eq('ida.project', $qb->createNamedParameter($project)))
            ->andWhere($qb->expr()->eq('ida.change', $qb->createNamedParameter('add')))
            ->andWhere($qb->expr()->like('ida.pathname', $qb->createNamedParameter($stagingPathnamePrefix)))
            ->orderBy('ida.pathname', 'ASC') // Order by pathname
            ->orderBy('ida.timestamp', 'DESC'); // Then order by timestamp

        //logger('ida')->debug('getDataChangeLastAddTimestamps: sql=' . Access::getRawSQL($qb));

        // Get results
        $results = $qb->execute()->fetchAll();

        // Use array_unique to keep only the latest timestamp for each pathname
        $finalResults = [];
        foreach ($results as $row) {
            $fullPathname = $row['pathname'];
            // Store only the latest timestamp for each pathname
            if (!isset($finalResults[$fullPathname])) {
                $finalResults[$fullPathname] = $row['timestamp'];
            }
        }

        logger('ida')->debug('getDataChangeLastAddTimestamps:' . 'results=' . count($finalResults));

        if (!empty($finalResults)) {
            reset($finalResults);
            $firstPathname = key($finalResults);
            $firstTimestamp = current($finalResults);
            logger('ida')->debug('getDataChangeLastAddTimestamp:' . 'result1: pathname=' . $firstPathname . ' timestamp=' . $firstTimestamp);
        }

        return $finalResults;
    }

    /**
     * Fetch all IDA frozen file records belonging to the specified project and
     * with pathnames within the specified scope, returning a dict with the full
     * frozen folder pathname as key and the record as an array of values.
     * 
     * @param string $project  the project to which the files should belong
     * @param string $scope    the scope that pathnames should begin with
     * 
     * @return array [ pathname => array, ... ]
     */
    public function getIdaFrozenFileDetails(string $project, string $scope): array {

        logger('ida')->debug('getIdaFrozenFileDetails:' . 'project=' . $project . ' scope=' . $scope);

        // Get QueryBuilder instance from Nextcloud's DB connection
        $qb = $this->db->getQueryBuilder();

        // Define the pathname prefix
        $pathnamePrefix = $scope . '%';

        // Build the query
        $qb->select('*')
            ->from('ida_frozen_file', 'ida')
            ->where($qb->expr()->eq('ida.project', $qb->createNamedParameter($project)))
            ->andWhere($qb->expr()->isNull('ida.removed'))
            ->andWhere($qb->expr()->isNull('ida.cleared'))
            ->andWhere($qb->expr()->like('ida.pathname', $qb->createNamedParameter($pathnamePrefix)))
            ->orderBy('ida.id', 'DESC');

        //logger('ida')->debug('getIdaFrozenFileDetails: sql=' . Access::getRawSQL($qb));

        // Get results
        $results = $qb->execute()->fetchAll();

        // Use array_unique to keep only the latest timestamp for each pathname
        $finalResults = [];
        foreach ($results as $row) {
            $frozenPathname = '/' . $project . $row['pathname'];
            if (!isset($finalResults[$frozenPathname])) {
                $finalResults[$frozenPathname] = $row;
                //logger('ida')->debug('getIdaFrozenFileDetails: frozenPathname=' . $frozenPathname . ' row=' . json_encode($row));
            }
        }

        logger('ida')->debug('getIdaFrozenFileDetails:' . 'results=' . count($finalResults));

        if (!empty($finalResults)) {
            reset($finalResults);
            $firstPathname = key($finalResults);
            $firstDetails = current($finalResults);
            logger('ida')->debug('getIdaFrozenFileDetails:' . 'result1: pathname=' . $firstPathname . ' details=' . json_encode($firstDetails));
        }

        return $finalResults;
    }

}
