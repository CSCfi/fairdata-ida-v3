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

namespace OCA\IDA\Controller;

use OCA\IDA\Db\FrozenFile;
use OCA\IDA\Db\FrozenFileMapper;
use OCA\IDA\Util\API;
use OCA\IDA\Util\Access;
use OCA\IDA\Util\Constants;
use OCA\IDA\Util\Generate;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Http\StreamResponse;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\IConfig;
use OCP\IRequest;
use OC\Files\Filesystem;
use OC\Files\View;
use Psr\Log\LoggerInterface;
use Exception;

use function OCP\Log\logger;

/**
 * Frozen File Controller
 */
class FrozenFileController extends Controller
{
    protected FrozenFileMapper $fileMapper;
    protected string $userId;
    protected IConfig          $config;
    protected View $fsView;
    private LoggerInterface $logger;

    /**
     * Creates the AppFramwork Controller
     *
     * @param string           $appName    name of the app
     * @param IRequest         $request    request object
     * @param FrozenFileMapper $fileMapper file mapper
     * @param string           $userId     userid
     * @param IConfig          $config     Nextcloud configuration
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function __construct($appName, IRequest $request, FrozenFileMapper $fileMapper, $userId, $config, LoggerInterface $logger) {
        parent::__construct($appName, $request);
        $this->fileMapper = $fileMapper;
        $this->userId = $userId;
        $this->config = $config;
        $this->logger = $logger;
        $this->fsView = Filesystem::getView();
        Filesystem::init($userId, '/');
    }

    /**
     * Retrieve all files associated with an optional action, and/or restricted to one or more projects (if admin)
     *
     * Restricted to the project access scope of the user.
     *
     * @param string $pid      the PID of an action
     * @param string $projects a comma separated list of project names, with no whitespace
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getFiles($pid = null, $projects = null) {

        $this->logger->debug('getFiles:' . ' pid=' . $pid . ' projects=' . $projects);

        try {

            try {
                API::validateStringParameter('pid', $pid);
                API::validateStringParameter('projects', $projects);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            $queryProjects = null;

            // Special case to retrieve all file details for all actions for one or more projects, used for admin operations only

            if (($this->userId === 'admin') && ($pid === "all") && ($projects)) {
                $pid = null;
            }

            // Initialize set of projects to any specified in request

            if ($projects) {
                $queryProjects = Access::cleanProjectList($projects);
            }

            // If user is not admin, get user projects and verify user belongs to at least one project, limiting
            // query to the intersection of user projects and any specified projects

            if ($this->userId !== 'admin') {

                $userProjects = Access::getUserProjects();

                if ($userProjects === null) {
                    return API::forbiddenErrorResponse('Session user does not belong to any projects.');
                }

                // If any projects are specified with the request, reduce the user project list to the
                // intersection of the input projects and allowed user projects

                if ($queryProjects && $userProjects) {
                    $queryProjects = implode(',', array_intersect(explode(',', $userProjects), explode(',', $queryProjects)));
                }

                // Else set the project list to the list of user projects

                else {
                    $queryProjects = $userProjects;
                }
            }

            $this->logger->debug('getFiles:' . ' queryProjects=' . $queryProjects);

            // If the user is not admin and the intersection with any explicitly speciied projects
            // and user projects is empty, return an empty array.

            if ($this->userId !== 'admin' && ($queryProjects === '')) {
                return new DataResponse(array());
            }

            $fileEntities = $this->fileMapper->findActionFiles($pid, $queryProjects);

            if (is_null($fileEntities) || empty($fileEntities)) {
                return new DataResponse(array());
            }

            // NOTE: it is possible for a repair action to have no associated files, if after re-scanning
            // the project frozen area there no longer exist any files in the frozen area.

            $this->logger->debug('getFiles: writing action file details as JSON to memory buffer');

            $temp = fopen('php://memory', 'w');
            API::outputArrayAsJSON($temp, $fileEntities);
            rewind($temp);

            // Free up memory
            $fileEntities = null;

            return new StreamResponse($temp);
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Retrieve the latest frozen file record based on the provided file PID
     *
     * Restricted to the project access scope of the user.
     *
     * @param string $pid the PID of the file
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getFile($pid, $includeInactive = false) {

        $this->logger->debug('getFile:' . ' pid=' . $pid);

        try {

            try {
                API::verifyRequiredStringParameter('pid', $pid);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            $projects = null;

            // If user is not admin, verify access rights
            if ($this->userId != 'admin') {

                // Get user projects and verify user belongs to at least one project
                $userProjects = Access::getUserProjects();

                if ($userProjects === null) {
                    return API::forbiddenErrorResponse('The current user does not belong to any projects.');
                } // Else set the project list to the list of user projects
                else {
                    $projects = $userProjects;
                }
            }

            $fileEntity = $this->fileMapper->findFile($pid, $projects, $includeInactive);

            if ($fileEntity === null) {
                return API::notFoundErrorResponse('The specified file was not found.');
            }

            return new DataResponse($fileEntity);
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Retrieve the latest created frozen file record based on the provided Nextcloud node ID
     *
     * Restricted to the project access scope of the user.
     *
     * @param string $node the Nextcloud node ID of the file
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getFileByNextcloudNodeId($node, $includeInactive = false) {

        $this->logger->debug('getFileByNextcloudNodeId:' . ' node=' . $node);

        try {

            try {
                API::verifyRequiredStringParameter('node', $node);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            $projects = null;

            // If user is not admin, verify access rights
            if ($this->userId != 'admin') {

                // Get user projects and verify user belongs to at least one project
                $userProjects = Access::getUserProjects();

                if ($userProjects === null) {
                    return API::forbiddenErrorResponse('The current user does not belong to any projects.');
                } // Else set the project list to the list of user projects
                else {
                    $projects = $userProjects;
                }
            }

            $fileEntity = $this->fileMapper->findByNextcloudNodeId($node, $projects, $includeInactive);

            if ($fileEntity === null) {
                return API::notFoundErrorResponse('The specified file was not found.');
            }

            return new DataResponse($fileEntity);
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Retrieve the latest frozen file record based on its project pathname
     *
     * @param string $project  the project to which the file belongs
     * @param string $pathname the pathname of the file
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getFileByProjectPathname($project, $pathname, $includeInactive = false) {

        try {
            try {
                API::verifyRequiredStringParameter('project', $project);
                API::verifyRequiredStringParameter('pathname', $pathname);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            $projects = null;

            // If user is not admin, verify access rights
            if ($this->userId != 'admin') {

                // Get user projects and verify user belongs to at least one project
                $userProjects = Access::getUserProjects();

                if ($userProjects === null) {
                    return API::forbiddenErrorResponse('The current user does not belong to any projects.');
                } // Else set the project list to the list of user projects
                else {
                    $projects = $userProjects;
                }
            }

            $fileEntity = $this->fileMapper->findByProjectPathname($project, $pathname, $projects, $includeInactive);

            if ($fileEntity === null) {
                return API::notFoundErrorResponse('The specified file was not found.');
            }

            return new DataResponse($fileEntity);
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Create a new frozen file record
     *
     * Restricted to admin and PSO users for the specified project.
     *
     * @param string $action     the PID of the project with which the file is associated
     * @param string $project    the project to which the file belongs
     * @param string $pathname   the relative pathname of the file
     * @param int    $node       the Nextcloud node ID of the file
     * @param int    $size       the size of the file
     * @param string $checksum   the checksum of a file
     * @param string $metadata   timestamp indicating when metadata for file was successfully published or updated
     * @param string $replicated timestamp indicating when the file was successfully replicated
     * @param string $removed    timestamp indicating when the file was removed from the frozen space
     * @param string $cleared    timestamp indicating when the file was cleared (as part of a cleared action)
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function createFile($action, $project, $pathname, $node = null, $size = null, $checksum = null,
                               $metadata = null, $replicated = null, $removed = null, $cleared = null) {

        $this->logger->info(
            'createFile:'
            . ' action=' . $action
            . ' project=' . $project
            . ' pathname=' . $pathname
            . ' node=' . $node
        );

        try {
            try {
                API::verifyRequiredStringParameter('action', $action);
                API::verifyRequiredStringParameter('project', $project);
                API::verifyRequiredStringParameter('pathname', $pathname);
                API::validateIntegerParameter('node', $node);
                API::validateIntegerParameter('size', $size);
                API::validateStringParameter('checksum', $checksum);
                API::validateTimestamp($metadata);
                API::validateTimestamp($replicated);
                API::validateTimestamp($removed);
                API::validateTimestamp($cleared);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            // Restrict to admin and PSO user for the specified project
            if ($this->userId != 'admin' && $this->userId != Constants::PROJECT_USER_PREFIX . $project) {
                return API::forbiddenErrorResponse();
            }

            if ($node === null) {
                // Consider whether we should get the Nextcloud node ID based on project and pathname...?
                $nextcloudNodeId = '0';
            }
            else {
                $nextcloudNodeId = $node;
            }

            $fileEntity = new FrozenFile();
            $fileEntity->setAction($action);
            $fileEntity->setNode($nextcloudNodeId);
            $fileEntity->setPid(Generate::newPid('f' . $nextcloudNodeId));
            $fileEntity->setFrozen(Generate::newTimestamp());
            $fileEntity->setProject($project);
            $fileEntity->setPathname($pathname);

            // Set all allowed specified parameter values

            if ($size) {
                $fileEntity->setSize(0 + $size);
            }
            $checksum = trim($checksum);
            if ($checksum) {
                // Ensure only the checksum value portion is stored if the checksum was provided as a URI
                if ($checksum[0] === 's' && substr($checksum, 0, 7) === "sha256:") {
                    $fileEntity->setChecksum(substr($checksum, 7));
                }
                else {
                    $fileEntity->setChecksum($checksum);
                }
            }
            if ($metadata) {
                $fileEntity->setMetadata($metadata);
            }
            if ($replicated) {
                $fileEntity->setReplication($replicated);
            }
            if ($removed) {
                $fileEntity->setRemoved($removed);
            }
            if ($cleared) {
                $fileEntity->setCleared($cleared);
            }

            return new DataResponse($this->fileMapper->insert($fileEntity));
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Update the latest existing frozen file record with the specified PID
     *
     * Restricted to admin and PSO users for the project specified for the action.
     *
     * @param string $pid        the PID of the file
     * @param string $size       the size of a file
     * @param string $modified   timestamp indicating when the file was last modified
     * @param string $frozen     timestamp indicating when the file was frozen
     * @param string $checksum   the checksum of a file
     * @param string $metadata   timestamp indicating when metadata for file was successfully published or updated
     * @param string $replicated timestamp indicating when the file was successfully replicated
     * @param string $removed    timestamp indicating when the file was removed from the frozen space
     * @param string $cleared    timestamp indicating when the file was cleared (as part of a cleared action)
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function updateFile($pid, $size = null, $modified = null, $frozen = null, $checksum = null,
                               $metadata = null, $replicated = null, $removed = null, $cleared = null) {

        $this->logger->info(
            'updateFile:'
            . ' pid=' . $pid
            . ' size=' . $size
            . ' modified=' . $modified
            . ' frozen=' . $frozen
            . ' checksum=' . $checksum
            . ' metadata=' . $metadata
            . ' replicated=' . $replicated
            . ' removed=' . $removed
            . ' cleared=' . $cleared
        );

        try {
            try {
                API::verifyRequiredStringParameter('pid', $pid);
                API::validateIntegerParameter('size', $size, true);
                API::validateStringParameter('checksum', $checksum, true);
                API::validateTimestamp($modified, true);
                API::validateTimestamp($frozen, true);
                API::validateTimestamp($metadata, true);
                API::validateTimestamp($replicated, true);
                API::validateTimestamp($removed, true);
                API::validateTimestamp($cleared, true);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            $fileEntity = $this->fileMapper->findFile($pid, null, true);

            if ($fileEntity === null) {
                return API::notFoundErrorResponse('The specified file was not found.');
            }

            // Restrict to admin and PSO user for the specified project. 

            if ($this->userId != 'admin' && $this->userId != Constants::PROJECT_USER_PREFIX . $fileEntity->getProject()) {
                return API::forbiddenErrorResponse('Session user does not have permission to modify the specified file.');
            }

            // Clear all specified parameter values defined explicitly as the string 'null'

            if ($size === 'null') {
                $fileEntity->setSize(null); $size = null;
            }
            if ($modified === 'null') {
                $fileEntity->setModified(null); $modified = null;
            }
            if ($frozen === 'null') {
                $fileEntity->setFrozen(null); $frozen = null;
            }
            if ($checksum === 'null') {
                $fileEntity->setChecksum(null); $checksum = null;
            }
            if ($metadata === 'null') {
                $fileEntity->setMetadata(null); $metadata = null;
            }
            if ($replicated === 'null') {
                $fileEntity->setReplicated(null); $replicated = null;
            }
            if ($removed === 'null') {
                $fileEntity->setRemoved(null); $removed = null;
            }
            if ($cleared === 'null') {
                $fileEntity->setCleared(null); $cleared = null;
            }

            // Set all allowed specified parameter values and update database record

            if ($size) {
                $fileEntity->setSize(0 + $size);
            }
            $checksum = trim($checksum);
            if ($checksum) {
                // Ensure only the checksum value portion is stored if the checksum was provided as a URI
                if ($checksum[0] === 's' && substr($checksum, 0, 7) === "sha256:") {
                    $fileEntity->setChecksum(substr($checksum, 7));
                }
                else {
                    $fileEntity->setChecksum($checksum);
                }
            }
            if ($modified) {
                $fileEntity->setModified($modified);
            }
            if ($frozen) {
                $fileEntity->setFrozen($frozen);
            }
            if ($metadata) {
                $fileEntity->setMetadata($metadata);
            }
            if ($replicated) {
                $fileEntity->setReplicated($replicated);
            }
            if ($removed) {
                $fileEntity->setRemoved($removed);
            }
            if ($cleared) {
                $fileEntity->setCleared($cleared);
            }

            return new DataResponse($this->fileMapper->update($fileEntity));
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Delete all existing frozen file records with the specified PID
     *
     * Restricted to admin and PSO users for the project specified for the action.
     *
     * @param string $pid the PID of the file
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function deleteFile($pid) {

        $this->logger->info('deleteFile: pid=' . $pid);

        try {
            try {
                API::verifyRequiredStringParameter('pid', $pid);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            $fileEntity = $this->fileMapper->findFile($pid, null, true);

            if ($fileEntity === null) {
                return API::notFoundErrorResponse('The specified file was not found.');
            }

            // Restrict to admin and PSO user for the specified project. 

            if ($this->userId != 'admin' && $this->userId != Constants::PROJECT_USER_PREFIX . $fileEntity->getProject()) {
                return API::forbiddenErrorResponse('Session user does not have permission to modify the specified file.');
            }

            $this->fileMapper->deleteFile($pid);

            return API::successResponse('File ' . $pid . ' deleted.');
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Set the title of the specified project
     *
     * Restricted to admin or PSO user
     *
     * @param string $project the project name
     * @param string $title the project title
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function setProjectTitle($project, $title) {

        $this->logger->debug(
            'setProjectTitle:'
            . ' project=' . $project
            . ' title=' . $title
            . ' userID=' . $this->userId
        );

        try {
            try {
                API::verifyRequiredStringParameter('project', $project);
                API::verifyRequiredStringParameter('title', $title);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            // Restrict to admin and PSO user for the specified project. 

            if ($this->userId != 'admin' && $this->userId != Constants::PROJECT_USER_PREFIX . $project) {
                return API::forbiddenErrorResponse();
            }

            if (!file_exists(self::buildFilesFolderPathname($project))) {
                return API::badRequestErrorResponse('The specified project was not found.');
            }

            $username = Constants::PROJECT_USER_PREFIX . $project;
            $password = $this->config->getSystemValueString('PROJECT_USER_PASS');
            $titleFileURI = $this->config->getSystemValueString('FILE_API') . '/' . $username . '/TITLE';

            // Initialize IDA change mode from client (e.g. UI) if it was provided in request, else default to 'api'
            $idaMode = 'api';
		    if (isset($_SERVER['HTTP_IDA_MODE'])) {
			    $values = explode(',', $_SERVER['HTTP_IDA_MODE']);
			    $idaMode = $values[0];
		    }

            $ch = curl_init($titleFileURI);

            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
            curl_setopt($ch, CURLOPT_HTTPHEADER, array(
                'IDA-Mode: ' . $idaMode,
                'IDA-Authenticated-User: ' . $this->userId
            ));
            curl_setopt($ch, CURLOPT_USERPWD, "$username:$password");
            curl_setopt($ch, CURLOPT_HTTPAUTH, CURLAUTH_ANY);
            curl_setopt($ch, CURLOPT_UNRESTRICTED_AUTH, true);
            curl_setopt($ch, CURLOPT_FRESH_CONNECT, true);
            curl_setopt($ch, CURLOPT_FAILONERROR, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $title);

            $response = curl_exec($ch);

            if ($response === false) {
                $this->logger->error(
                    'setProjectTitle: PUT'
                    . ' titleFileURI=' . $titleFileURI
                    . ' user=' . $this->userId
                    . ' psoUser=' . $username
                    . ' mode=' . $idaMode
                    . ' curl_errno=' . curl_errno($ch)
                    . ' response=' . $response
                );
                curl_close($ch);
                throw new Exception('Failed to set title for project "' . $project . '"');
            }

            curl_close($ch);

            $this->logger->info(
                'setProjectTitle:'
                . ' project=' . $project
                . ' title=' . $title
                . ' userID=' . $this->userId
            );

            return API::successResponse($title, $debug=true);
        }
        catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Retrieve the title of the specified project, if defined, else return project name
     *
     * Restricted to the project access scope of the user.
     *
     * @param string $project the project name
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getProjectTitle($project) {

        $this->logger->debug('getProjectTitle: project=' . $project);

        $userProjects = null;

        try {
            try {
                API::verifyRequiredStringParameter('project', $project);
            }
            catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            // If user is not admin, verify access rights
            if ($this->userId != 'admin') {

                // Get user projects and verify user belongs to at least one project
                $userProjects = Access::getUserProjects();

                if ($userProjects === null || !in_array($project, explode(",", $userProjects))) {
                    return API::forbiddenErrorResponse();
                }
            }

            $filesFolderPathname = self::buildFilesFolderPathname($project);

            if (!file_exists($filesFolderPathname)) {
                return API::badRequestErrorResponse('The specified project was not found.');
            }

            $title = $project;

            $titleFilePathname = $filesFolderPathname . '/TITLE';

            if (file_exists($titleFilePathname)) {
                $fileTitle = file_get_contents($titleFilePathname);
                if ($fileTitle) {
                    $title = trim($fileTitle);
                    // If for some reason we fail to retrieve the title from the file, we
                    // will return the project name as the default title
                }
            }

            // We only log success responses for title requests if debug logging is enabled, otherwise, no logging is done. This is to
            // prevent log files from being filled needlessly with success response messages, since title requests are done frequently.
            $this->logger->debug('getProjectTitle:' . ' project=' . $project . ' title=' . $title);
            return API::successResponse($title, $debug=true);
        }
        catch (Exception $e) {
            // Always return successfully, defaulting to project name
            $this->logger->error(
                'getProjectTitle:'
                . ' project=' . $project
                . ' userId=' . $this->userId
                . ' userProjects=' . $userProjects
                . ' error=' . $e->getMessage()
            );
            return API::successResponse($project, $debug=true);
        }
    }

    /**
     * Builds and returns the full pathname of the files folder for the specified project.
     *
     * @param string $project the project name
     *
     * @return string
     */
    protected static function buildFilesFolderPathname($project) {
        $dataRootPathname = \OC::$server->getConfig()->getSystemValue('datadirectory', '/mnt/storage_vol01/ida');
        $filesFolderPathname = $dataRootPathname . '/' . Constants::PROJECT_USER_PREFIX . $project . '/files';
        logger('ida')->debug('buildFilesFolderPathname: filesFolderPathname=' . $filesFolderPathname);
        return ($filesFolderPathname);
    }
    
}
