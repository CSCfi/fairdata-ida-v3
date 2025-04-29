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

use OCA\IDA\Db\DataChange;
use OCA\IDA\Db\DataChangeMapper;
use OCA\IDA\Util\API;
use OCA\IDA\Util\Access;
use OCA\IDA\Util\Constants;
use OCA\IDA\Util\Generate;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\IConfig;
use OCP\IRequest;
use OCP\IUserSession;
use OCA\IDA\Util\NotProjectUser;
use Psr\Log\LoggerInterface;
use Exception;
use function OCP\Log\logger;

/**
 * Data Change Event Controller
 */
class DataChangeController extends Controller
{
    protected DataChangemapper $dataChangeMapper;
    protected string           $userId;
    protected IConfig          $config;
    protected LoggerInterface $logger;

    /**
     * Creates the AppFramwork Controller
     *
     * @param string           $appName           name of the app
     * @param IRequest         $request           request object
     * @param DataChangeMapper $dataChangeMapper  data change event mapper
     * @param string           $userId            userid
     * @param IConfig          $config            global configuration
     * @param LoggerInterface  $logger            IDA app logger
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function __construct(
        string $appName,
        IRequest $request,
        DataChangeMapper $dataChangeMapper,
        string $userId,
        IConfig $config,
        LoggerInterface $logger
    ) {
        parent::__construct($appName, $request);
        $this->dataChangeMapper = $dataChangeMapper;
        $this->userId = $userId;
        $this->config = $config;
        $this->logger = $logger;
    }

    public function getConfig()
    {
        return $this->config;
    }

    /**
     * Return the timestamp for when a project was added to the IDA service
     *
     * @param string $project  the project name
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getInitialization($project)
    {
        $this->logger->debug('getInitialization project=' . $project);

        try {

            try {
                API::verifyRequiredStringParameter('project', $project);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            // Ensure the project exists

            $datadir = $this->config->getSystemValue('datadirectory');

            if ($datadir === null) {
                throw new Exception('Failed to get data storage root pathname');
            }

            $projectRoot = $datadir . '/' . Constants::PROJECT_USER_PREFIX . $project . '/';

            $this->logger->debug('getLastDataChange: projectRoot=' . $projectRoot);

            if (! is_dir($projectRoot)) {
                return API::notFoundErrorResponse('Unknown project.');
            }

            // If user is not admin, nor PSO user, verify user belongs to project

            if ($this->userId !== 'admin' && $this->userId !== Constants::PROJECT_USER_PREFIX . $project) {
                Access::verifyIsAllowedProject($project);
            }

            return new DataResponse($this->dataChangeMapper->getInitializationDetails($project));

        } catch (NotProjectUser $e) {
            return API::forbiddenErrorResponse('Session user does not belong to the specified project');
        } catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Return the last recorded data change event for a project, if any, else return details
     * from original legacy data migration event.
     *
     * @param string $project  the project name
     * @param string $user     get last change by a particular user, if specified
     * @param string $change   get last change event for a particular change, if specified
     * @param string $mode     get last change event for a particular mode, if specified
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getLastDataChange($project, $user = null, $change = null, $mode = null)
    {
        $this->logger->debug('getLastDataChange:'
            . ' project=' . $project
            . ' user=' . $user
            . ' change=' . $change
            . ' mode=' . $mode
        );

        try {

            try {
                API::verifyRequiredStringParameter('project', $project);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            // Ensure the project exists

            $datadir = $this->config->getSystemValue('datadirectory');

            if ($datadir === null) {
                throw new Exception('Failed to get data storage root pathname');
            }

            $projectRoot = $datadir . '/' . Constants::PROJECT_USER_PREFIX . $project . '/';

            $this->logger->debug('getLastDataChange: projectRoot=' . $projectRoot);

            if (! is_dir($projectRoot)) {
                return API::notFoundErrorResponse('Unknown project.');
            }

            // If user is not admin, nor PSO user, verify user belongs to project

            if ($this->userId !== 'admin' && $this->userId !== Constants::PROJECT_USER_PREFIX . $project) {
                Access::verifyIsAllowedProject($project);
            }

            return new DataResponse($this->dataChangeMapper->getLastDataChangeDetails($project, $user, $change, $mode));

        } catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Return one or more recorded data change events for a project, if any, else return details
     * from original legacy data migration event.
     *
     * @param string $project  the project name
     * @param string $user     limit changes to a particular user, if specified
     * @param string $change   limit changes to a particular data change, if specified
     * @param string $mode     limit changes to a particular mode, if specified
     * @param int    $limit    the number of changes to return, null = unlimited
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getDataChanges($project, $user = null, $change = null, $mode = null, $limit = null)
    {
        $this->logger->debug(
            'getDataChanges:'
            . ' project=' . $project
            . ' user=' . $user
            . ' change=' . $change
            . ' mode=' . $mode
            . ' limit=' . $limit
        );

        try {

            try {
                API::verifyRequiredStringParameter('project', $project);
                API::validateIntegerParameter('limit', $limit);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            // Ensure the project exists

            $datadir = $this->config->getSystemValue('datadirectory');

            if ($datadir === null) {
                throw new Exception('Failed to get data storage root pathname');
            }

            $projectRoot = $datadir . '/' . Constants::PROJECT_USER_PREFIX . $project . '/';

            $this->logger->debug('getDataChanges: projectRoot=' . $projectRoot);

            if (! is_dir($projectRoot)) {
                return API::notFoundErrorResponse('Unknown project.');
            }

            // If user is not admin, nor PSO user, verify user belongs to project

            if ($this->userId !== 'admin' && $this->userId !== Constants::PROJECT_USER_PREFIX . $project) {
                Access::verifyIsAllowedProject($project);
            }

            $response = new DataResponse($this->dataChangeMapper->getDataChangeDetails($project, $user, $change, $mode, $limit));

            $this->logger->debug(
                'getDataChanges: response data='
                . json_encode($response->getData())
                . ' status=' . json_encode($response->getStatus())
                . ' headers=' . json_encode($response->getHeaders())
            );

            return $response;

        } catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    /**
     * Record a data change event for a project.
     *
     * Restricted to admin or PSO user for project.
     *
     * @param string $project    the project name
     * @param string $user       the user making the change
     * @param string $change     the data change
     * @param string $pathname   the pathname of the scope of the change
     * @param string $target     the target pathname, required for rename, move, or copy change, error otherwise if not null
     * @param string $timestamp  the datetime of the event (defaults to current datetime if not specified)
     * @param string $mode       the mode via which the change was made (defaults to 'api')
     *
     * @return DataResponse
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function recordDataChange($project, $user, $change, $pathname, $target = null, $timestamp = null, $mode = null)
    {
        $this->logger->debug(
            'recordDataChange:'
            . ' project=' . $project
            . ' user=' . $user
            . ' change=' . $change
            . ' pathname=' . $pathname
            . ' target=' . $target
            . ' timestamp=' . $timestamp
            . ' mode=' . $mode
        );

        try {

            try {
                API::verifyRequiredStringParameter('project', $project);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            try {
                API::verifyRequiredStringParameter('user', $user);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            try {
                API::verifyRequiredStringParameter('change', $change);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            try {
                API::verifyRequiredStringParameter('pathname', $pathname);
            } catch (Exception $e) {
                return API::badRequestErrorResponse($e->getMessage());
            }

            if ($timestamp) {
                try {
                    API::validateStringParameter('timestamp', $timestamp);
                } catch (Exception $e) {
                    return API::badRequestErrorResponse($e->getMessage());
                }
                try {
                    API::validateTimestamp($timestamp);
                } catch (Exception $e) {
                    return API::badRequestErrorResponse($e->getMessage());
                }
            } else {
                $timestamp = Generate::newTimestamp();
            }

            // Ensure the project exists

            $datadir = $this->config->getSystemValue('datadirectory');

            if ($datadir === null) {
                throw new Exception('Failed to get data storage root pathname');
            }

            $projectRoot = $datadir . '/' . Constants::PROJECT_USER_PREFIX . $project . '/';

            $this->logger->debug('getDataChanges: projectRoot=' . $projectRoot);

            if (! is_dir($projectRoot)) {
                return API::notFoundErrorResponse('Unknown project.');
            }

            if ($this->userId !== 'admin' && $this->userId !== Constants::PROJECT_USER_PREFIX . $project) {
                return API::forbiddenErrorResponse();
            }

            if (! in_array($change, DataChange::CHANGES)) {
                return API::badRequestErrorResponse('Invalid change specified.');
            }

            if (in_array($change, DataChange::TARGET_CHANGES) && ($target === null || $target === '')) {
                return API::badRequestErrorResponse('Target must be specified.');
            }

            if ($mode) {
                try {
                    API::validateStringParameter('mode', $mode);
                } catch (Exception $e) {
                    return API::badRequestErrorResponse($e->getMessage());
                }
                if (! in_array($mode, DataChange::MODES)) {
                    return API::badRequestErrorResponse('Invalid mode specified.');
                }
            }

            // Only record changes to project data, where pathname begins with either staging or frozen folder, unless initialization
            if ($change !== 'init') {
                if (! (  strpos($pathname, '/' . $project . '/') === 0
                      || strpos($pathname, '/' . $project . Constants::STAGING_FOLDER_SUFFIX . '/') === 0)) {
                    return API::badRequestErrorResponse('Pathname must begin with staging or frozen root folder');
                }
            }

            if (! (  $target == null
                  || strpos($target, '/' . $project . '/') === 0
                  || strpos($target, '/' . $project . Constants::STAGING_FOLDER_SUFFIX . '/') === 0)) {
                return API::badRequestErrorResponse('Target must begin with staging or frozen root folder');
            }

            return new DataResponse($this->dataChangeMapper->recordDataChangeDetails($project, $user, $change, $pathname, $target, $timestamp, $mode));

        } catch (Exception $e) {
            return API::serverErrorResponse($e->getMessage());
        }
    }

    public static function processNextcloudOperation($change, $pathname, $target = null, $idaUser = null, $idaMode = null, $context = null, $logger = null) {

        if ($logger == null) {
            $logger = logger('ida');
        }

        try {

            $logger->debug(
                'processNextcloudOperation:'
                . ' change=' . $change
                . ' pathname=' . $pathname
                . ' target=' . $target
                . ' idaUser=' . $idaUser
                . ' idaMode=' . $idaMode
                . ' context=' . $context
                );

            if ($pathname === null) {
                throw new Exception('processNextcloudOperation: pathname parameter cannot be null');
            }

            // Ignore appdata changes
            if (strpos($pathname, '/appdata') === 0 || strpos($pathname, 'appdata') === 0) {
                $logger->debug('processNextcloudOperation: ignoring appdata change');
                return;
            }

            // Ignore PSO account changes
            if (strpos($pathname, '/' . Constants::PROJECT_USER_PREFIX) === 0 || strpos($pathname, Constants::PROJECT_USER_PREFIX) === 0) {
                $logger->debug('processNextcloudOperation: ignoring PSO account change');
                return;
            }

            // Ignore internal operations not bound to an authenticated user session
            try {
                $currentUser = \OC::$server->get(IUserSession::class)->getUser()->getUID();
            }
            catch (Exception $e) {
                throw new Exception('ida', 'processNextcloudOperation: failed to retrieve current user');
            }
            if ($currentUser === null || trim($currentUser) === '') {
                // Allow backend changes to be processes, e.g. from occ files:scan
                if ($idaUser === 'service' && $idaMode === 'system') {
                    $currentUser = 'service';
                } else {
                    $logger->debug('processNextcloudOperation: ignoring non-authenticated user change');
                    return;
                }
            }

            if ($change === null) {
                throw new Exception('processNextcloudOperation: change parameter cannot be null');
            }

            if (! in_array($change, \OCA\IDA\Db\DataChange::CHANGES)) {
                throw new Exception('processNextcloudOperation: unsupported change: ' . $change);
            }

		    if ($change === 'rename' && $target && dirname($pathname) != dirname($target)) {
			    $change = 'move';
		    }

            if (strpos($pathname, '//') === 0) {
                $pathname = '/' . ltrim($pathname, '/');
            }

            try {
                $project = rtrim(explode('/', ltrim($pathname, '/'))[0], '+');
            } catch (Exception $e) {
                throw new Exception('processNextcloudOperation: Failed to extract project name from pathname ' . $pathname . ': ' . $e->getMessage());
            }

            if ($project === null || $project === '') {
                throw new Exception('processNextcloudOperation: project name cannot be null');
            }

            $logger->debug(
                'processNextcloudOperation:'
                . ' project=' . $project
                . ' change=' . $change
                . ' pathname=' . $pathname
                . ' target=' . $target
                . ' idaUser=' . $idaUser
                . ' currentUser=' . $currentUser
                );

            $config = \OC::$server->get(IConfig::class);
            if ($config === null) {
                throw new Exception('processNextcloudOperation: Failed to get Nextcloud configuration');
            }

            $datadir = $config->getSystemValue('datadirectory');
            if ($datadir === null) {
                throw new Exception('processNextcloudOperation: Failed to get data storage root pathname');
            }
            $logger->debug('processNextcloudOperation: datadir=' . $datadir);

            if ($datadir === null) {
                throw new Exception('processNextcloudOperation: Failed to get data storage root pathname');
            }

            $fqdn = gethostname();

            if ($fqdn === False || $fqdn === 'localhost') {
                throw new Exception('processNextcloudOperation: Failed to get fqdn');
            }

            $idaRootUrl = 'https://' . $fqdn;

            $logger->debug('processNextcloudOperation: idaRootUrl=' . $idaRootUrl);

            $psopass = $config->getSystemValue('PROJECT_USER_PASS');
            if (!$psopass) {
                throw new Exception('processNextcloudOperation: Failed to get data PSO password');
            }

            // If the parsing of the project name from the path does not derive to a valid project, tested by constructing
            // the PSO user root directory pathname, ignore the request, as the pathname does not start with either a staging
            // or frozen folder and does not pertain to a project data change but some other internal operation
    
            $projectRoot = $datadir . '/' . Constants::PROJECT_USER_PREFIX . $project . '/';
            $logger->debug('processNextcloudOperation: projectRoot=' . $projectRoot);
    
            if (! is_dir($projectRoot)) {
                $logger->debug('processNextcloudOperation: ignoring non-project data change - no PSO root found');
                return;
            }
    
            // If the pathname is not within either the staging or frozen folder, ignore the change
            if (! (  strpos($pathname, '/' . $project . '/') === 0
                  || strpos($pathname, '/' . $project . Constants::STAGING_FOLDER_SUFFIX . '/') === 0)) {
                $logger->debug('processNextcloudOperation: ignoring non-project data change - pathname not within staging or frozen root folder');
                return;
            }

            if ($idaUser) {
                $user = $idaUser;
            } else {
                $user = $currentUser;
            }

            if ($idaMode) {
                $mode = strtolower($idaMode);
            } else {
                $mode = 'api';
            }

            $username = Constants::PROJECT_USER_PREFIX . $project;
            $password =  $psopass;
            $requestURL = $idaRootUrl . '/apps/ida/api/dataChanges';
            $postbody = json_encode(
                array(
                    'project'  => $project,
                    'user'     => $user,
                    'change'   => $change,
                    'pathname' => $pathname,
                    'target'   => $target,
                    'mode'     => $mode
                )
            );

            $logger->debug(
                'processNextcloudOperation:'
                . ' username=' . $username
                . ' password=' . $password
                . ' requestURL=' . $requestURL
                . ' postbody=' . $postbody
            );

            $ch = curl_init($requestURL);

            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
            curl_setopt($ch, CURLOPT_USERPWD, "$username:$password");
            curl_setopt($ch, CURLOPT_POSTFIELDS, $postbody);
            curl_setopt($ch, CURLOPT_HEADER, false);
            curl_setopt($ch, CURLOPT_HTTPHEADER,
                array(
                    'Accept: application/json',
                    'Content-Type: application/json',
                    'Content-Length: ' . strlen($postbody)
                )
            );
            curl_setopt($ch, CURLOPT_FRESH_CONNECT, true);
            curl_setopt($ch, CURLOPT_FAILONERROR, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30);

            $logger->debug('processNextcloudOperation: curlinfo=' . json_encode($ch));
    
            $response = curl_exec($ch);

            $logger->debug('processNextcloudOperation: curlinfo=' . json_encode(curl_getinfo($ch)));

            if ($response === false) {
                $logger->error('processNextcloudOperation: ' . ' curl_errno=' . curl_errno($ch) . ' response=' . $response);
                curl_close($ch);
                throw new Exception('Failed to record data change from Nextcloud operation');
            }

            curl_close($ch);
        }
        catch (Exception $e) {
            // Log any errors but don't prevent Nextcloud from otherwise working
            $logger->error('Error encountered trying to record data change: ' . $e->getMessage());
        }
    }
}
