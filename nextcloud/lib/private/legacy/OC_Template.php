<?php

/**
 * SPDX-FileCopyrightText: 2016-2024 Nextcloud GmbH and Nextcloud contributors
 * SPDX-FileCopyrightText: 2016 ownCloud, Inc.
 * SPDX-License-Identifier: AGPL-3.0-only
 */
use OC\TemplateLayout;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\EventDispatcher\IEventDispatcher;
use Psr\Log\LoggerInterface;

require_once __DIR__ . '/template/functions.php';

/**
 * This class provides the templates for ownCloud.
 */
class OC_Template extends \OC\Template\Base {
	/** @var string */
	private $renderAs; // Create a full page?

	/** @var string */
	private $path; // The path to the template

	/** @var array */
	private $headers = []; //custom headers

	/** @var string */
	protected $app; // app id

	/**
	 * Constructor
	 *
	 * @param string $app app providing the template
	 * @param string $name of the template file (without suffix)
	 * @param string $renderAs If $renderAs is set, OC_Template will try to
	 *                         produce a full page in the according layout. For
	 *                         now, $renderAs can be set to "guest", "user" or
	 *                         "admin".
	 * @param bool $registerCall = true
	 */
	public function __construct($app, $name, $renderAs = TemplateResponse::RENDER_AS_BLANK, $registerCall = true) {
		$theme = OC_Util::getTheme();

		$requestToken = (OC::$server->getSession() && $registerCall) ? \OCP\Util::callRegister() : '';
		$cspNonce = \OCP\Server::get(\OC\Security\CSP\ContentSecurityPolicyNonceManager::class)->getNonce();

		$parts = explode('/', $app); // fix translation when app is something like core/lostpassword
		$l10n = \OC::$server->getL10N($parts[0]);
		/** @var \OCP\Defaults $themeDefaults */
		$themeDefaults = \OCP\Server::get(\OCP\Defaults::class);

		[$path, $template] = $this->findTemplate($theme, $app, $name);

		// Set the private data
		$this->renderAs = $renderAs;
		$this->path = $path;
		$this->app = $app;

		parent::__construct(
			$template,
			$requestToken,
			$l10n,
			$themeDefaults,
			$cspNonce,
		);
	}


	/**
	 * find the template with the given name
	 * @param string $name of the template file (without suffix)
	 *
	 * Will select the template file for the selected theme.
	 * Checking all the possible locations.
	 * @param string $theme
	 * @param string $app
	 * @return string[]
	 */
	protected function findTemplate($theme, $app, $name) {
		// Check if it is a app template or not.
		if ($app !== '') {
			$dirs = $this->getAppTemplateDirs($theme, $app, OC::$SERVERROOT, OC_App::getAppPath($app));
		} else {
			$dirs = $this->getCoreTemplateDirs($theme, OC::$SERVERROOT);
		}
		$locator = new \OC\Template\TemplateFileLocator($dirs);
		$template = $locator->find($name);
		$path = $locator->getPath();
		return [$path, $template];
	}

	/**
	 * Add a custom element to the header
	 * @param string $tag tag name of the element
	 * @param array $attributes array of attributes for the element
	 * @param string $text the text content for the element. If $text is null then the
	 *                     element will be written as empty element. So use "" to get a closing tag.
	 */
	public function addHeader($tag, $attributes, $text = null) {
		$this->headers[] = [
			'tag' => $tag,
			'attributes' => $attributes,
			'text' => $text
		];
	}

	/**
	 * Process the template
	 * @return string
	 *
	 * This function process the template. If $this->renderAs is set, it
	 * will produce a full page.
	 */
	public function fetchPage($additionalParams = null) {
		$data = parent::fetchPage($additionalParams);

		if ($this->renderAs) {
			$page = new TemplateLayout($this->renderAs, $this->app);

			if (is_array($additionalParams)) {
				foreach ($additionalParams as $key => $value) {
					$page->assign($key, $value);
				}
			}

			// Add custom headers
			$headers = '';
			foreach (OC_Util::$headers as $header) {
				$headers .= '<' . \OCP\Util::sanitizeHTML($header['tag']);
				if (strcasecmp($header['tag'], 'script') === 0 && in_array('src', array_map('strtolower', array_keys($header['attributes'])))) {
					$headers .= ' defer';
				}
				foreach ($header['attributes'] as $name => $value) {
					$headers .= ' ' . \OCP\Util::sanitizeHTML($name) . '="' . \OCP\Util::sanitizeHTML($value) . '"';
				}
				if ($header['text'] !== null) {
					$headers .= '>' . \OCP\Util::sanitizeHTML($header['text']) . '</' . \OCP\Util::sanitizeHTML($header['tag']) . '>';
				} else {
					$headers .= '/>';
				}
			}

			$page->assign('headers', $headers);

			$page->assign('content', $data);
			return $page->fetchPage($additionalParams);
		}

		return $data;
	}

	/**
	 * Include template
	 *
	 * @param string $file
	 * @param array|null $additionalParams
	 * @return string returns content of included template
	 *
	 * Includes another template. use <?php echo $this->inc('template'); ?> to
	 * do this.
	 */
	public function inc($file, $additionalParams = null) {
		return $this->load($this->path . $file . '.php', $additionalParams);
	}

	/**
	 * Shortcut to print a simple page for users
	 * @param string $application The application we render the template for
	 * @param string $name Name of the template
	 * @param array $parameters Parameters for the template
	 * @return boolean|null
	 */
	public static function printUserPage($application, $name, $parameters = []) {
		$content = new OC_Template($application, $name, 'user');
		foreach ($parameters as $key => $value) {
			$content->assign($key, $value);
		}
		print $content->printPage();
	}

	/**
	 * Shortcut to print a simple page for admins
	 * @param string $application The application we render the template for
	 * @param string $name Name of the template
	 * @param array $parameters Parameters for the template
	 * @return bool
	 */
	public static function printAdminPage($application, $name, $parameters = []) {
		$content = new OC_Template($application, $name, 'admin');
		foreach ($parameters as $key => $value) {
			$content->assign($key, $value);
		}
		return $content->printPage();
	}

	/**
	 * Shortcut to print a simple page for guests
	 * @param string $application The application we render the template for
	 * @param string $name Name of the template
	 * @param array|string $parameters Parameters for the template
	 * @return bool
	 */
	public static function printGuestPage($application, $name, $parameters = []) {
		$content = new OC_Template($application, $name, $name === 'error' ? $name : 'guest');
		foreach ($parameters as $key => $value) {
			$content->assign($key, $value);
		}
		return $content->printPage();
	}

	/**
	 * Print a fatal error page and terminates the script
	 * @param string $error_msg The error message to show
	 * @param string $hint An optional hint message - needs to be properly escape
	 * @param int $statusCode
	 * @suppress PhanAccessMethodInternal
	 */
	public static function printErrorPage($error_msg, $hint = '', $statusCode = 500) {
		if (\OC::$server->getAppManager()->isEnabledForUser('theming') && !\OC_App::isAppLoaded('theming')) {
			\OC_App::loadApp('theming');
		}


		if ($error_msg === $hint) {
			// If the hint is the same as the message there is no need to display it twice.
			$hint = '';
		}
		$errors = [['error' => $error_msg, 'hint' => $hint]];

		http_response_code($statusCode);

        // IDA MODIFICATION START
		header('Content-Type: text/plain; charset=utf-8');
		print("$error_msg $hint");
		die();
        // IDA MODIFICATION END

		try {
			// Try rendering themed html error page
			$response = new TemplateResponse(
				'',
				'error',
				['errors' => $errors],
				TemplateResponse::RENDER_AS_ERROR,
				$statusCode,
			);
			$event = new BeforeTemplateRenderedEvent(false, $response);
			\OC::$server->get(IEventDispatcher::class)->dispatchTyped($event);
			print($response->render());
		} catch (\Throwable $e1) {
			$logger = \OCP\Server::get(LoggerInterface::class);
			$logger->error('Rendering themed error page failed. Falling back to un-themed error page.', [
				'app' => 'core',
				'exception' => $e1,
			]);

			try {
				// Try rendering unthemed html error page
				$content = new \OC_Template('', 'error', 'error', false);
				$content->assign('errors', $errors);
				$content->printPage();
			} catch (\Exception $e2) {
				// If nothing else works, fall back to plain text error page
				$logger->error("$error_msg $hint", ['app' => 'core']);
				$logger->error('Rendering un-themed error page failed. Falling back to plain text error page.', [
					'app' => 'core',
					'exception' => $e2,
				]);

				header('Content-Type: text/plain; charset=utf-8');
				print("$error_msg $hint");
			}
		}
		die();
	}

	/**
	 * print error page using Exception details
	 * @param Exception|Throwable $exception
	 * @param int $statusCode
	 * @return bool|string
	 * @suppress PhanAccessMethodInternal
	 */
	public static function printExceptionErrorPage($exception, $statusCode = 503) {
		$debug = false;
		http_response_code($statusCode);
		try {
			$debug = \OC::$server->getSystemConfig()->getValue('debug', false);
			$serverLogsDocumentation = \OC::$server->getSystemConfig()->getValue('documentation_url.server_logs', '');
			$request = \OC::$server->getRequest();
			$content = new \OC_Template('', 'exception', 'error', false);
			$content->assign('errorClass', get_class($exception));
			$content->assign('errorMsg', $exception->getMessage());
			$content->assign('errorCode', $exception->getCode());
			$content->assign('file', $exception->getFile());
			$content->assign('line', $exception->getLine());
			$content->assign('exception', $exception);
			$content->assign('debugMode', $debug);
			$content->assign('serverLogsDocumentation', $serverLogsDocumentation);
			$content->assign('remoteAddr', $request->getRemoteAddress());
			$content->assign('requestID', $request->getId());
			$content->printPage();
		} catch (\Exception $e) {
			try {
				$logger = \OCP\Server::get(LoggerInterface::class);
				$logger->error($exception->getMessage(), ['app' => 'core', 'exception' => $exception]);
				$logger->error($e->getMessage(), ['app' => 'core', 'exception' => $e]);
			} catch (Throwable $e) {
				// no way to log it properly - but to avoid a white page of death we send some output
				self::printPlainErrorPage($e, $debug);

				// and then throw it again to log it at least to the web server error log
				throw $e;
			}

			self::printPlainErrorPage($e, $debug);
		}
		die();
	}

	private static function printPlainErrorPage(\Throwable $exception, bool $debug = false) {
		header('Content-Type: text/plain; charset=utf-8');
		print("Internal Server Error\n\n");
		print("The server encountered an internal error and was unable to complete your request.\n");
		print("Please contact the server administrator if this error reappears multiple times, please include the technical details below in your report.\n");
		print("More details can be found in the server log.\n");

		if ($debug) {
			print("\n");
			print($exception->getMessage() . ' ' . $exception->getFile() . ' at ' . $exception->getLine() . "\n");
			print($exception->getTraceAsString());
		}
	}
}
