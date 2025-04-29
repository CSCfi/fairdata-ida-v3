<!-- IDA MODIFICATION START -->
<?php

use function OCP\Log\logger;
use Firebase\JWT\JWT;
use OCP\IConfig;

$CURRENT_LANGUAGE = $_GET['language'] ?? null;

// Check SSO session language
if (!$CURRENT_LANGUAGE || !in_array($CURRENT_LANGUAGE, ['en', 'fi', 'sv'])) {
    // try session language
    $hostname = $_SERVER['SERVER_NAME'] ?? $_SERVER['HTTP_HOST'] ?? getenv('HOSTNAME') ?? gethostname();
    if ($hostname) {
        $domain = substr($hostname, strpos($hostname, ".") + 1);
        $prefix = preg_replace('/[^a-zA-Z0-9]/', '_', $domain);
        $cookie = $prefix . '_fd_sso_session';
        if (isset($_COOKIE[$cookie])) {
            try {
                $key = \OC::$server->get(IConfig::class)->getSystemValue('SSO_KEY');
                $session = JWT::decode($_COOKIE[$cookie], $key, ['HS256']);
                if (!empty($session->language)) {
                    $CURRENT_LANGUAGE = $session->language;
                }
            } catch (\Exception $e) {}
        }
    }
}
    
// Else try browser language
if (!$CURRENT_LANGUAGE || !in_array($CURRENT_LANGUAGE, ['en', 'fi', 'sv'])) {
    $browserLang = substr($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '', 0, 2);
    $CURRENT_LANGUAGE = $browserLang;
}
    
// Fallback
if (!in_array($CURRENT_LANGUAGE, ['en', 'fi', 'sv'])) {
    $CURRENT_LANGUAGE = 'en';
}

$IDA_LANGUAGES = array(
    array(
        "short" => "en",
        "full" => "English (EN)"
    ),
    array(
        "short" => "fi",
        "full" => "Finnish (FI)"
    ),
    array(
        "short" => "sv",
        "full" => "Swedish (SV)"
    )
);

function SSOActive()
{
    if (\OC::$server->get(IConfig::class)->getSystemValue('SSO_AUTHENTICATION') === true) {
        return true;
    }
    if (isset($_GET['sso_authentication'])) {
        if ($_GET['sso_authentication'] === 'true') {
            return true;
        }
    }
    return false;
}

function FDWEActive()
{
    return \OC::$server->get(IConfig::class)->getSystemValue('FDWE_URL', null) != null;
}

function localLoginActive()
{
    if (isset($_GET['local_login'])) {
        if ($_GET['local_login'] === 'true') {
            return true;
        }
    }
    if (sharePasswordActive()) {
        return true;
    }
    if (!SSOActive()) {
        return true;
    }
    return \OC::$server->get(IConfig::class)->getSystemValue('LOCAL_LOGIN') === true;
}

function sharePasswordActive()
{
    return (strpos($_SERVER['REQUEST_URI'], '/s/NOT-FOR-PUBLICATION-') !== false);
}

function localLoginOrSharePasswordActive()
{
    return (localLoginActive() || sharePasswordActive());
}
?>

<!DOCTYPE html>
<html
    class="ng-csp"
    data-placeholder-focus="false"
    lang="<?php p($_['language']); ?>"
    data-locale="<?php p($_['locale']); ?>" translate="no">
<head
    <?php if ($_['user_uid']) { ?>
    data-user="<?php p($_['user_uid']); ?>"
    data-user-displayname="<?php p($_['user_displayname']); ?>"
    <?php } ?>
    data-requesttoken="<?php p($_['requesttoken']); ?>">
    <meta charset="utf-8">
    <title>
        <?php p(!empty($_['pageTitle']) ? $_['pageTitle'] . ' – ' : '');
        p($theme->getTitle()); ?>
    </title>
    <meta name="csp-nonce" nonce="<?php p($_['cspNonce']); /* Do not pass into "content" to prevent exfiltration */ ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0 <?php if (isset($_['viewport_maximum_scale'])) {
                                                                                                p(', maximum-scale=' . $_['viewport_maximum_scale']);
                                                                                            } ?>">
    <?php if ($theme->getiTunesAppId() !== '') { ?>
        <meta name="apple-itunes-app" content="app-id=<?php p($theme->getiTunesAppId()); ?>">
    <?php } ?>
    <meta name="theme-color" content="<?php p($theme->getColorPrimary()); ?>">
    <link rel="icon" href="<?php print_unescaped(image_path('core', 'favicon.ico')); /* IE11+ supports png */ ?>">
    <link rel="apple-touch-icon" href="<?php print_unescaped(image_path('core', 'favicon-touch.png')); ?>">
    <link rel="mask-icon" sizes="any" href="<?php print_unescaped(image_path('core', 'favicon-mask.svg')); ?>" color="<?php p($theme->getColorPrimary()); ?>">
    <link rel="manifest" href="<?php print_unescaped(image_path('core', 'manifest.json')); ?>" crossorigin="use-credentials">
    <?php emit_css_loading_tags($_); ?>
    <?php emit_script_loading_tags($_); ?>
    <?php print_unescaped($_['headers']); ?>
    <link rel="stylesheet" href="/themes/ida/core/css/fairdata.css">
    <?php if (SSOActive()) : ?>
        <link nonce="<?php p(\OC::$server->getContentSecurityPolicyNonceManager()->getNonce()) ?>" rel="stylesheet" href="<?php p(\OC::$server->get(IConfig::class)->getSystemValue('SSO_API')); ?>/notification.css">
        <script nonce="<?php p(\OC::$server->getContentSecurityPolicyNonceManager()->getNonce()) ?>" src="<?php p(\OC::$server->get(IConfig::class)->getSystemValue('SSO_API')); ?>/notification.js"></script>
    <?php endif; ?>
    <link rel="stylesheet" href="/themes/ida/core/css/ida-guest.css">
    <?php if (localLoginOrSharePasswordActive()) : /* increase container width if local login is enabled */ ?>
        <style type="text/css">
            .fd-content {
                width: 100%;
                max-width: 1500px;
            }
        </style>
    <?php endif; ?>
    <style type="text/css">
        body {
            font: 500 16px/25px "Lato" !important;
            color: black;
        }
    </style>
    <?php if (FDWEActive()) : ?>
        <meta name="fdwe-service" content="IDA">
        <?php if (strpos($_SERVER["REQUEST_URI"], "NOT-FOR-PUBLICATION-") !== false) : ?>
            <meta name="fdwe-scope" content="FILES / SHARE / ACCESS / PASSWORD">
        <?php else : ?>
            <meta name="fdwe-scope" content="HOME">
        <?php endif; ?>
        <script nonce="<?php p(\OC::$server->getContentSecurityPolicyNonceManager()->getNonce()) ?>" src="<?php p(\OC::$server->get(IConfig::class)->getSystemValue('FDWE_URL')); ?>"></script>
    <?php endif; ?>
</head>
<body id="<?php p($_['bodyid']); ?>">
    <?php include 'layout.noscript.warning.php'; ?>
    <?php include 'layout.initial-state.php'; ?>
    <div id="languageChoiceDropdown" class="language-selector-mobile">
        <div class="language-choice-toggle active">
            <?php
            $activeLanguageIndex = array_search($CURRENT_LANGUAGE, array_column($IDA_LANGUAGES, 'short'));
            if ($activeLanguageIndex !== FALSE) {
                p($IDA_LANGUAGES[$activeLanguageIndex]["full"]);
            }
            ?>
            <img src="<?php print_unescaped(image_path('', 'expand.png')); ?>" id="expandIcon" alt="Expand">
        </div>
        <div id="languageChoices" class="language-choices">
            <?php
            $languagesToDisplay = array_filter($IDA_LANGUAGES, function ($lang) use ($CURRENT_LANGUAGE) {
                return $lang["short"] != $CURRENT_LANGUAGE;
            });
            foreach ($languagesToDisplay as $lang) {
                print_unescaped('<button aria-label="Change language to ' . $lang["full"] . '" class="language-choice fd-button" tabindex="0" data-language-code="' . $lang["short"] . '">' . $lang["full"] . '</button>');
            }
            ?>
        </div>
    </div>
    <div class="fd-header container-fluid">
        <div class="row no-gutter">
            <div class="col-8">
                <img src="<?php print_unescaped(image_path('', 'ida-logo-header.png')); ?>" class="logo">
            </div>
            <?php if (!sharePasswordActive()) : ?>
                <div class="login-selector-wrapper col-4">
                    <?php if (SSOActive()) : ?>
                        <a href="<?php p(\OC::$server->get(IConfig::class)->getSystemValue('SSO_API')) ?>/login?service=IDA&redirect_url=<?php p(\OC::$server->get(IConfig::class)->getSystemValue('IDA_HOME')) ?>&language=<?php p($CURRENT_LANGUAGE) ?>">
                            <button class="fd-button login-button"><?php if ($CURRENT_LANGUAGE == "fi") : ?>Kirjaudu<?php elseif ($CURRENT_LANGUAGE == "sv") : ?>Logga in<?php else : ?>Login<?php endif; ?></button>
                        </a>
                    <?php endif; ?>
                    <div class="language-selector-container">
                        <?php
                        foreach ($languagesToDisplay as $lang) {
                            print_unescaped('<span aria-label="Change language to ' . $lang["full"] . '" class="language-choice" tabindex="0" data-language-code="' . $lang["short"] . '">' . $lang["short"] . '</span>');
                        }
                        ?>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </div>
    <div class="fd-content container">
        <?php if (localLoginOrSharePasswordActive()) : ?>
            <div class="col-lg-4 col-md-12 flex-center-md fd-col" style="max-width: 375px; padding-top: 25px;">
                <!-- Local login form will be inserted into this main element by Nextcloud -->
                <main id="ida-local-login" style="display: <?php echo localLoginActive() ? 'block' : 'none'; ?>;">
                    <h1 class="hidden-visually"><?php p($theme->getName()); ?></h1>
                    <?php print_unescaped($_['content']); ?>
                </main>
            </div>
        <?php endif; ?>
        <?php if (!sharePasswordActive()) : ?>
            <?php if ($CURRENT_LANGUAGE == "fi") : ?>
                <div class="<?php if (localLoginActive()) p('col-lg-4');
                            else p('col-lg-6'); ?> col-md-12 fd-col">
                    <h2>Tervetuloa Fairdata IDA -palveluun</h2>
                    <p>Fairdata IDA on turvallinen ja maksuton tutkimusdatan säilytyspalvelu, jota tarjotaan Suomen korkeakouluille ja valtion tutkimuslaitoksille. IDA kuuluu opetus- ja kulttuuriministeriön järjestämään Fairdata-palvelukokonaisuuteen.</p>
                    <p>Säilytystila on projektikohtaista. IDAssa säilytettävä data voidaan muiden Fairdata-palvelujen avulla kuvailla tutkimusaineistoksi ja julkaista.</p>
                    <p><a href="https://www.fairdata.fi/ida/" rel="noopener" target="_blank">Käytön aloitus ja käyttöoppaat</a></p>
                </div>
                <div class="<?php if (localLoginActive()) p('col-lg-4');
                            else p('col-lg-6'); ?> col-md-12 padding-top: 0px; fd-col">
                    <div class="row card-login active">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>IDA</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'ida.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">Siirrä datasi IDA-palveluun. Voit järjestellä dataa ja jäädyttää sen, kun data on valmis säilytykseen.</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 align-center">
                            <img src="<?php print_unescaped(image_path('', 'arrow.png')); ?>" class="arrow">
                        </div>
                    </div>
                    <div class="row card-login">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>Qvain</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'qvain.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">Kun datasi on jäädytetty, kuvaile ja julkaise se Qvain-työkalulla.</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 align-center">
                            <img src="<?php print_unescaped(image_path('', 'arrow.png')); ?>" class="arrow">
                        </div>
                    </div>
                    <div class="row card-login">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>Etsin</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'etsin.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">Etsin-palvelussa voit hakea ja ladata julkaistuja tutkimusaineistoja.</p>
                        </div>
                    </div>
                </div>
            <?php elseif ($CURRENT_LANGUAGE == "sv") : ?>
                <div class="<?php if (localLoginActive()) p('col-lg-4');
                            else p('col-lg-6'); ?> col-md-12 fd-col">
                    <h2>Välkommen till Fairdata IDA</h2>
                    <p>Fairdata IDA är en trygg tjänst för lagring av forskningsdata. Tjänsten erbjuds utan kostnad för universitet, yrkeshögskolor och forskningsinstitut i Finland. IDA är en del av Fairdata-tjänsterna som erbjuds av Undervisnings- och kulturministeriet.</p>
                    <p>Bevaringsutrymmet i IDA tilldelas projekt. Data som finns i IDA kan dokumenteras och publiceras som dataset med hjälp av andra Fairdata-tjänster.</p>
                    <p><a href="https://www.fairdata.fi/en/ida/" rel="noopener" target="_blank">Hur man tar i bruk och använder IDA (på engelska)</a></p>
                </div>
                <div class="<?php if (localLoginActive()) p('col-lg-4');
                            else p('col-lg-6'); ?> col-md-12 padding-top: 0px; fd-col">
                    <div class="row card-login active">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>IDA</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'ida.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">Flytta dina data till IDA, ordna dem och frys dem.</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 align-center">
                            <img src="<?php print_unescaped(image_path('', 'arrow.png')); ?>" class="arrow">
                        </div>
                    </div>
                    <div class="row card-login">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>Qvain</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'qvain.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">Då de är frysta kan du dokumentera och publicera dem med hjälp av Qvain.</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 align-center">
                            <img src="<?php print_unescaped(image_path('', 'arrow.png')); ?>" class="arrow">
                        </div>
                    </div>
                    <div class="row card-login">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>Etsin</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'etsin.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">Du kan upptäcka och ladda ner dataset via Etsin.</p>
                        </div>
                    </div>
                </div>
            <?php else : ?>
                <div class="<?php if (localLoginActive()) p('col-lg-4');
                            else p('col-lg-6'); ?> col-md-12 fd-col">
                    <h2>Welcome to Fairdata IDA</h2>
                    <p>Fairdata IDA is a continuous research data storage service organized by the Ministry of Education and Culture. The service is offered free of charge to Finnish universities, universities of applied sciences and state research institutes.</p>
                    <p>IDA enables uploading, organizing, and sharing research data within a project group and storing the data in an immutable state. The data stored in IDA can be included in research datasets which are described and made publicly available for download via other Fairdata services.</p>
                    <p><a href="https://www.fairdata.fi/en/ida/" rel="noopener" target="_blank">How to start using IDA and user guides</a></p>
                </div>
                <div class="<?php if (localLoginActive()) p('col-lg-4');
                            else p('col-lg-6'); ?> col-md-12 padding-top: 0px; fd-col">
                    <div class="row card-login active">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>IDA</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'ida.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">You store data in IDA. You can organize your data and freeze it in a final immutable state.</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 align-center">
                            <img src="<?php print_unescaped(image_path('', 'arrow.png')); ?>" class="arrow">
                        </div>
                    </div>
                    <div class="row card-login">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>Qvain</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'qvain.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">After freezing, you describe your data and publish it using Qvain.</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12 align-center">
                            <img src="<?php print_unescaped(image_path('', 'arrow.png')); ?>" class="arrow">
                        </div>
                    </div>
                    <div class="row card-login">
                        <div class="col-sm-2 col-6 align-center align-right-sm">
                            <span>Etsin</span>
                        </div>
                        <div class="col-sm-2 col-6 align-center align-left-sm">
                            <img src="<?php print_unescaped(image_path('', 'etsin.png')); ?>">
                        </div>
                        <div class="col-sm-8 col-12">
                            <p style="padding-left: 10px; opacity: 1;">You can discover and download datasets through Etsin.</p>
                        </div>
                    </div>
                </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>
    <div class="fd-footer container-fluid">
        <?php if ($CURRENT_LANGUAGE == "fi") : ?>
            <div class="row no-gutters">
                <div class="col col-lg-4 col-md-12 col-sm-12 col-12">
                    <span>Fairdata
                        <a class="fd-link fd-link-footer" rel="noopener" target="_blank" href="https://www.fairdata.fi/en/fairdata-services/">
                            <img width="175px" src="/themes/ida/core/img/supporting-eosc.jpg" alt="Supporting eosc" class=" logo"="">
                        </a>
                    </span>
                    <p>Fairdata-palvelut jär­jes­tää <strong>opetus- ja kulttuuriministeriö</strong> ja toimittaa <strong>CSC – Tieteen tieto­tekniikan keskus Oy</strong></p>
                </div>
                <div class="col padding-right col-lg-2 col-md-3 col-sm-6 offset-lg-1">
                    <span>Tietoa</span>
                    <p><a href="https://www.fairdata.fi/kayttopolitiikat-ja-ehdot/" rel="noopener" target="_blank">Käyttöpolitiikat ja ehdot</a></p>
                    <p><a href="https://www.fairdata.fi/sopimukset/" rel="noopener" target="_blank">Sopimukset ja tietosuoja</a></p>
                </div>
                <div class="col padding-right col-lg-2 col-md-3 col-sm-6 col-6">
                    <span>Saavutettavuus</span>
                    <p><a href="https://www.fairdata.fi/saavutettavuus/" rel="noopener" target="_blank">Saavutettavuus</a></p>
                </div>
                <div class="col col-lg-2 col-md-3 col-sm-6 col-6">
                    <span>Ota yhteyttä</span>
                    <p><a href="mailto:servicedesk@csc.fi">servicedesk@csc.fi</a></p>
                </div>
                <div class="col col-lg-1 col-md-3 col-sm-6 col-6">
                    <span>Seuraa</span>
                    <p style="display: flex; align-items: center;">
                        <a href="https://bsky.app/profile/fairdata.fi" rel="noopener" target="_blank" title="Seuraa meitä Blueskyssa">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 568 501" width="20px" style="margin-right: 4px; vertical-align: middle;">
                                <path fill="#1185FE" d="M123.121 33.664C188.241 82.553 258.281 181.68 284 234.873c25.719-53.192 95.759-152.32 160.879-201.21C491.866-1.611 568-28.906 568 57.947c0 17.346-9.945 145.713-15.778 166.555-20.275 72.453-94.155 90.933-159.875 79.748C507.222 323.8 536.444 388.56 473.333 453.32c-119.86 122.992-172.272-30.859-185.702-70.281-2.462-7.227-3.614-10.608-3.631-7.733-.017-2.875-1.169.506-3.631 7.733-13.43 39.422-65.842 193.273-185.702 70.281-63.111-64.76-33.89-129.52 80.986-149.071-65.72 11.185-139.6-7.295-159.875-79.748C9.945 203.659 0 75.291 0 57.946 0-28.906 76.135-1.612 123.121 33.664Z"></path>
                            </svg>@fairdata.fi
                        </a>
                    </p>
                    <p><a href="https://www.fairdata.fi/ajankohtaista/" rel="noopener" target="_blank">Uutiset</a></p>
                </div>
            </div>
        <?php elseif ($CURRENT_LANGUAGE == "sv") : ?>
            <div class="row no-gutters">
                <div class="col col-lg-4 col-md-12 col-sm-12 col-12">
                    <span>Fairdata
                        <a class="fd-link fd-link-footer" rel="noopener" target="_blank" href="https://www.fairdata.fi/en/fairdata-services/">
                            <img width="175px" src="/themes/ida/core/img/supporting-eosc.jpg" alt="Supporting eosc" class=" logo"="">
                        </a>
                    </span>
                    <p>Fairdata-tjänsterna erbjuds av <strong>ministeriet för utbildning och kultur</strong> och produceras av <strong>CSC - IT Center for Science Ltd.</strong></p>
                </div>
                <div class="col padding-right col-lg-2 col-md-3 col-sm-6 offset-lg-1">
                    <span>Information</span>
                    <p><a href="https://www.fairdata.fi/en/terms-and-policies/" rel="noopener" target="_blank">Villkor och policyer</a></p>
                    <p><a href="https://www.fairdata.fi/en/contracts-and-privacy/" rel="noopener" target="_blank">Kontrakt och integritet</a></p>
                </div>
                <div class="col padding-right col-lg-2 col-md-3 col-sm-6 col-6">
                    <span>Tillgänglighet</span>
                    <p><a href="https://www.fairdata.fi/en/accessibility/" rel="noopener" target="_blank">Tillgänglighet uttalande</a></p>
                </div>
                <div class="col col-lg-2 col-md-3 col-sm-6 col-6">
                    <span>Kontakt</span>
                    <p><a href="mailto:servicedesk@csc.fi">servicedesk@csc.fi</a></p>
                </div>
                <div class="col col-lg-1 col-md-3 col-sm-6 col-6">
                    <span>Följ</span>
                    <p style="display: flex; align-items: center;">
                        <a href="https://bsky.app/profile/fairdata.fi" rel="noopener" target="_blank" title="Följ oss på Bluesky">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 568 501" width="20px" style="margin-right: 4px; vertical-align: middle;">
                                <path fill="#1185FE" d="M123.121 33.664C188.241 82.553 258.281 181.68 284 234.873c25.719-53.192 95.759-152.32 160.879-201.21C491.866-1.611 568-28.906 568 57.947c0 17.346-9.945 145.713-15.778 166.555-20.275 72.453-94.155 90.933-159.875 79.748C507.222 323.8 536.444 388.56 473.333 453.32c-119.86 122.992-172.272-30.859-185.702-70.281-2.462-7.227-3.614-10.608-3.631-7.733-.017-2.875-1.169.506-3.631 7.733-13.43 39.422-65.842 193.273-185.702 70.281-63.111-64.76-33.89-129.52 80.986-149.071-65.72 11.185-139.6-7.295-159.875-79.748C9.945 203.659 0 75.291 0 57.946 0-28.906 76.135-1.612 123.121 33.664Z"></path>
                            </svg>@fairdata.fi
                        </a>
                    </p>
                    <p><a href="https://www.fairdata.fi/en/news/" rel="noopener" target="_blank">Nyheter</a></p>
                </div>
            </div>
        <?php else : ?>
            <div class="row no-gutters">
                <div class="col col-lg-4 col-md-12 col-sm-12 col-12">
                    <span>Fairdata
                        <a class="fd-link fd-link-footer" rel="noopener" target="_blank" href="https://www.fairdata.fi/en/fairdata-services/">
                            <img width="175px" src="/themes/ida/core/img/supporting-eosc.jpg" alt="Supporting eosc" class=" logo"="">
                        </a>
                    </span>
                    <p>The Fairdata services are offered by the<strong> Ministry of Education and Culture </strong>and produced by<strong> CSC – IT Center for Science Ltd.</strong></p>
                </div>
                <div class="col padding-right col-lg-2 col-md-3 col-sm-6 offset-lg-1">
                    <span>Information</span>
                    <p><a href="https://www.fairdata.fi/en/terms-and-policies/" rel="noopener" target="_blank">Terms and Policies</a></p>
                    <p><a href="https://www.fairdata.fi/en/contracts-and-privacy/" rel="noopener" target="_blank">Contracts and Privacy</a></p>
                </div>
                <div class="col padding-right col-lg-2 col-md-3 col-sm-6 col-6">
                    <span>Accessibility</span>
                    <p><a href="https://www.fairdata.fi/en/accessibility/" rel="noopener" target="_blank">Accessibility statement</a></p>
                </div>
                <div class="col col-lg-2 col-md-3 col-sm-6 col-6">
                    <span>Contact</span>
                    <p><a href="mailto:servicedesk@csc.fi">servicedesk@csc.fi</a></p>
                </div>
                <div class="col col-lg-1 col-md-3 col-sm-6 col-6">
                    <span>Follow</span>
                    <p style="display: flex; align-items: center;">
                        <a href="https://bsky.app/profile/fairdata.fi" rel="noopener" target="_blank" title="Follow us on Bluesky">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 568 501" width="20px" style="margin-right: 4px; vertical-align: middle;">
                                <path fill="#1185FE" d="M123.121 33.664C188.241 82.553 258.281 181.68 284 234.873c25.719-53.192 95.759-152.32 160.879-201.21C491.866-1.611 568-28.906 568 57.947c0 17.346-9.945 145.713-15.778 166.555-20.275 72.453-94.155 90.933-159.875 79.748C507.222 323.8 536.444 388.56 473.333 453.32c-119.86 122.992-172.272-30.859-185.702-70.281-2.462-7.227-3.614-10.608-3.631-7.733-.017-2.875-1.169.506-3.631 7.733-13.43 39.422-65.842 193.273-185.702 70.281-63.111-64.76-33.89-129.52 80.986-149.071-65.72 11.185-139.6-7.295-159.875-79.748C9.945 203.659 0 75.291 0 57.946 0-28.906 76.135-1.612 123.121 33.664Z"></path>
                            </svg>@fairdata.fi
                        </a>
                    </p>
                    <p><a href="https://www.fairdata.fi/en/news/" rel="noopener" target="_blank">What's new</a></p>
                </div>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
<!-- IDA MODIFICATION END -->