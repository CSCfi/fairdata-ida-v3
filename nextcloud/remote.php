<?php

/**
 * SPDX-FileCopyrightText: 2016-2024 Nextcloud GmbH and Nextcloud contributors
 * SPDX-FileCopyrightText: 2016 ownCloud, Inc.
 * SPDX-License-Identifier: AGPL-3.0-only
 */
require_once __DIR__ . '/lib/versioncheck.php';

use OCA\DAV\Connector\Sabre\ExceptionLoggerPlugin;
use Psr\Log\LoggerInterface;
use Sabre\DAV\Exception\ServiceUnavailable;
use Sabre\DAV\Server;
// IDA MODIFICATION START
use function OCP\Log\logger;
// IDA MODIFICATION END

/**
 * Class RemoteException
 * Dummy exception class to be use locally to identify certain conditions
 * Will not be logged to avoid DoS
 */
class RemoteException extends \Exception {
}

/**
 * @param Exception|Error $e
 */
function handleException($e) {
	try {
		$request = \OC::$server->getRequest();
		// in case the request content type is text/xml - we assume it's a WebDAV request
		$isXmlContentType = strpos($request->getHeader('Content-Type'), 'text/xml');
		if ($isXmlContentType === 0) {
			// fire up a simple server to properly process the exception
			$server = new Server();
			if (!($e instanceof RemoteException)) {
				// we shall not log on RemoteException
				$server->addPlugin(new ExceptionLoggerPlugin('webdav', \OC::$server->get(LoggerInterface::class)));
			}
			$server->on('beforeMethod:*', function () use ($e) {
				if ($e instanceof RemoteException) {
					switch ($e->getCode()) {
						case 503:
							throw new ServiceUnavailable($e->getMessage());
						case 404:
							throw new \Sabre\DAV\Exception\NotFound($e->getMessage());
					}
				}
				$class = get_class($e);
				$msg = $e->getMessage();
				throw new ServiceUnavailable("$class: $msg");
			});
			$server->exec();
		} else {
			$statusCode = 500;
			if ($e instanceof \OC\ServiceUnavailableException) {
				$statusCode = 503;
			}
			if ($e instanceof RemoteException) {
				// we shall not log on RemoteException
				OC_Template::printErrorPage($e->getMessage(), '', $e->getCode());
			} else {
				\OC::$server->get(LoggerInterface::class)->error($e->getMessage(), ['app' => 'remote','exception' => $e]);
				OC_Template::printExceptionErrorPage($e, $statusCode);
			}
		}
	} catch (\Exception $e) {
		OC_Template::printExceptionErrorPage($e, 500);
	}
}

/**
 * @param $service
 * @return string
 */
function resolveService($service) {
	$services = [
		'webdav' => 'dav/appinfo/v1/webdav.php',
		'dav' => 'dav/appinfo/v2/remote.php',
		'caldav' => 'dav/appinfo/v1/caldav.php',
		'calendar' => 'dav/appinfo/v1/caldav.php',
		'carddav' => 'dav/appinfo/v1/carddav.php',
		'contacts' => 'dav/appinfo/v1/carddav.php',
		'files' => 'dav/appinfo/v1/webdav.php',
		'direct' => 'dav/appinfo/v2/direct.php',
	];
	if (isset($services[$service])) {
		return $services[$service];
	}

	return \OC::$server->getConfig()->getAppValue('core', 'remote_' . $service);
}

try {
	require_once __DIR__ . '/lib/base.php';

	// All resources served via the DAV endpoint should have the strictest possible
	// policy. Exempted from this is the SabreDAV browser plugin which overwrites
	// this policy with a softer one if debug mode is enabled.
	header("Content-Security-Policy: default-src 'none';");

	if (\OCP\Util::needUpgrade()) {
		// since the behavior of apps or remotes are unpredictable during
		// an upgrade, return a 503 directly
		throw new RemoteException('Service unavailable', 503);
	}

	$request = \OC::$server->getRequest();
	$pathInfo = $request->getPathInfo();
	if ($pathInfo === false || $pathInfo === '') {
		throw new RemoteException('Path not found', 404);
	}
	if (!$pos = strpos($pathInfo, '/', 1)) {
		$pos = strlen($pathInfo);
	}
	$service = substr($pathInfo, 1, $pos - 1);

	// IDA MODIFICATION START
	//
	// If the request method has side effects, and the request URL path corresponds to a WebDAV URL, then
	//    Return 409 Conflict if:
	//        * the service is offline, OR
	//        * the service is suspended, OR
	//        * the specific project is suspended
	//    Return 403 Forbidden if:
	//        * the request affects the root frozen or staging folder, AND
	//        * the user is not the project share owner

	if (in_array($request->getMethod(), array('PUT', 'DELETE', 'MKCOL', 'COPY', 'MOVE', 'PROPPATCH', 'POST'))) {

        $suspended = false;

		$dataRootPathname = \OC::$server->getConfig()->getSystemValue('datadirectory', '/mnt/storage_vol01/ida');
        $serviceOfflinePathname = $dataRootPathname . '/control/OFFLINE';

		// Disallow request if service is offline

		if (file_exists($serviceOfflinePathname)) {
			logger('ida')->debug('remote.php: service is offline');
		    throw new RemoteException('Service unavailable. Please try again later.', 503);
	    }

		logger('ida')->debug('remote.php: pathInfo=' . $pathInfo);

		$parts = explode('/', $pathInfo);

		if ($parts[1] === 'dav' && $parts[2] === 'files') {

			logger('ida')->debug('remote.php: is WebDAV request');

	        $username = $parts[3];
	        $project = rtrim($parts[4], '+');
            $projectDataRootPathname  = $dataRootPathname . '/' . 'PSO_' . $project . '/files';
            $serviceSuspendedPathname = $dataRootPathname . '/control/SUSPENDED';
            $projectSuspendedPathname = $projectDataRootPathname . '/SUSPENDED';

			logger('ida')->debug(
				'remote.php:'
				. ' project=' . $project
				. ' username=' . $username
				. ' projectDataRootPathname=' . $projectDataRootPathname
				. ' serviceSuspendedPathname=' . $serviceSuspendedPathname
				. ' projectSuspendedPathname=' . $projectSuspendedPathname
			);

		    if (is_dir($projectDataRootPathname)) {

			    logger('ida')->debug('remote.php: project data root exists');

		        // Disallow request if request URL corresponds to either root frozen or staging folder
		        // and user is not PSO user

		        if (sizeOf($parts) === 5 && $username != 'PSO_' . $project) {
		            throw new RemoteException('Root project folders cannot be modified by project users', 403);
		        }

				// Check if either service or project is suspended

				if (file_exists($serviceSuspendedPathname)) {
			        logger('ida')->debug('remote.php: service is suspended');
		            $suspended = true;
				}

				if (file_exists($projectSuspendedPathname)) {
			            logger('ida')->debug('remote.php: project is suspended');
		                $suspended = true;
				}

		        // Disallow request if either service or project is suspended

	            if ($suspended) {
		            throw new RemoteException('Project suspended. Action not permitted.', 409);
	            }
		    }
		}
	}
	// IDA MODIFICATION END

	$file = resolveService($service);

	if (is_null($file)) {
		throw new RemoteException('Path not found', 404);
	}

	$file = ltrim($file, '/');

	$parts = explode('/', $file, 2);
	$app = $parts[0];

	// Load all required applications
	\OC::$REQUESTEDAPP = $app;
	OC_App::loadApps(['authentication']);
	OC_App::loadApps(['extended_authentication']);
	OC_App::loadApps(['filesystem', 'logging']);

	switch ($app) {
		case 'core':
			$file = OC::$SERVERROOT .'/'. $file;
			break;
		default:
			if (!\OC::$server->getAppManager()->isInstalled($app)) {
				throw new RemoteException('App not installed: ' . $app);
			}
			OC_App::loadApp($app);
			$file = OC_App::getAppPath($app) .'/'. $parts[1];
			break;
	}
	$baseuri = OC::$WEBROOT . '/remote.php/'.$service.'/';
	require_once $file;
} catch (Exception $ex) {
	handleException($ex);
} catch (Error $e) {
	handleException($e);
}
