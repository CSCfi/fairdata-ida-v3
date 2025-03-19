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

use \OCP\DB\QueryBuilder\IQueryBuilder;
use Exception;

/**
 * Various value generation methods
 */
class Generate
{
    /**
     * Generate a new PID, with optional suffix
     *
     * Current conventions used for suffixes:
     *    action PIDs are given the suffix 'a' + the Nextcloud node ID of the folder
     *    folder PIDs are given the suffix 'd' + the Nextcloud node ID
     *    file PIDs are given the suffix 'f' + the Nextcloud node ID
     *
     * @param string $suffix optional suffix to append to generated PID, limited to 10 characters in length
     *
     * @return string
     */
    public static function newPid($suffix = null) {
        
        // If suffix defined, limit to max 10 initial characters
       
        if ($suffix) {
            $suffix = substr($suffix, 0, 10);
        }
        
        $pid = uniqid("", true);
        $pid = str_replace('.', '', $pid);
        
        return $pid . $suffix;
    }
    
    /**
     * Generate ISO standard formatted timestamp string for current UTC time, or for UNIX epoch integer timestamp, if specified
     *
     * @param int epoch  A UNIX epoch integer timestamp (optional)
     * @return string
     */
    public static function newTimestamp($epoch = null) {
        if ($epoch !== null) {
            if (!is_int($epoch)) {
                throw new Exception('The specified Unix epoch value is invalid: ' . $epoch);
            }
            return gmdate('Y-m-d\TH:i:s\Z', $epoch);
        } else {
            return gmdate('Y-m-d\TH:i:s\Z');
        }
    }

    public static function rawSQL(IQueryBuilder $query) {

        if ($query) {

            $sql = $query->getSQL();
            $params =  $query->getParameters();

            foreach ($params as $key => $value) {

                // Prepare the placeholder (e.g., `:dcValue1`)
                $placeholder = ':' . $key;
    
                // Handle different data types
                if (is_string($value)) {
                    // Escape single quotes inside the string value and wrap in quotes
                    $escapedValue = "'" . str_replace("'", "''", $value) . "'";
                }
                elseif (is_array($value)) {
                    // Convert array to a comma-separated list and wrap each value in quotes if necessary
                    $escapedValue = implode(', ', array_map(function($item) {
                        return is_string($item) ? "'" . str_replace("'", "''", $item) . "'" : $item;
                    }, $value));
                }
                elseif (is_null($value)) {
                    // Convert null values to the SQL `NULL`
                    $escapedValue = 'NULL';
                }
                else {
                    // For integers, booleans, etc., just use the value directly
                    $escapedValue = $value;
                }
    
                // Replace the placeholder in the SQL string with the escaped value
                $sql = str_replace($placeholder, $escapedValue, $sql);
            }
    
            return $sql;
        }

        return null;
    }
}
