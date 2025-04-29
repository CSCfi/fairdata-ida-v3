/*
 * This file is part of the Fairdata IDA research data storage service.
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
 * author    CSC - IT Center for Science Ltd., Espoo Finland <servicedesk@csc.fi>
 * license   GNU Affero General Public License, version 3
 * link      https://www.fairdata.fi/en/ida
 */

// This file contains all programmatic changes to the Nextcloud UI not achieved by
// the IDA theme CSS stylesheet

import { getCurrentUser } from '@nextcloud/auth'
import { t } from '@nextcloud/l10n'
import { showError } from '@nextcloud/dialogs'
import IconDotsHorizontalCircleOutline from 'vue-material-design-icons/DotsHorizontalCircleOutline.vue'
import IconAlertCircleOutline from 'vue-material-design-icons/AlertCircleOutline.vue'
import { STAGING_FOLDER_SUFFIX } from './constants.js'
import { consoleDebug, renderSvgComponent, getProjectTitle, getNodeDetails, getActions, localizeTimestamp, hideElements, isFrozen } from './utils.js'

function getLanguageCode() {
    const rawLang = window.OC?.getLocale?.() || navigator.language || navigator.userLanguage || 'en';
    const lang = rawLang.toLowerCase().split(/[-_]/)[0];
    return (lang === 'fi' || lang === 'sv') ? lang : 'en';
}

function focusIsInForm() {
    const inForm = document.activeElement.matches('input, textarea, select, [contenteditable=true]');
    if (inForm) consoleDebug('User focus in in a form');
    return inForm;
}

function executeOnURLChange(callback) {

    let lastURL = location.href;

    const observeHistoryMethod = (method) => {
        const original = history[method];
        history[method] = function(...args) {
            const result = original.apply(this, args);
            if (lastURL !== location.href) {
                lastURL = location.href;
                callback();
            }
            return result;
        };
    };

    observeHistoryMethod('pushState');
    observeHistoryMethod('replaceState');

    window.addEventListener('popstate', () => {
        if (lastURL !== location.href) {
            lastURL = location.href;
            callback();
        }
    });
}

function fixLoginPage() {

    consoleDebug('fixLoginPage()');
    consoleDebug(window.location.pathname);

    // TODO don't call unless actually on the login page (check window location)

    // Handle click on language choice
    const languageChoices = document.querySelectorAll('.language-choice');
    languageChoices.forEach(function(languageChoice) {
        languageChoice.addEventListener('click', function() {
            const languageCode = this.getAttribute('data-language-code');
            window.location.href = '/login?language=' + languageCode;
        });
    });

    // Handle click on language choice toggle
    const languageChoiceToggle = document.querySelector('.language-choice-toggle');
    if (languageChoiceToggle) {
        languageChoiceToggle.addEventListener('click', function() {
                const languageChoicesElement = document.getElementById('languageChoices');
            const expandIcon = document.getElementById('expandIcon');
            let rotation = 180;
            // Toggle visibility of language choices
            if (languageChoicesElement.style.display === 'block') {
                rotation = 0;
                languageChoicesElement.style.display = 'none';
            } else {
                languageChoicesElement.style.display = 'block';
            }
            // Apply rotation transform to the icon
            expandIcon.style.transform = 'rotate(' + rotation + 'deg)';
        });
    }

    // Prevent automatic expansion of username input field
    const nameField = document.getElementById('user');
    if (nameField) {
        nameField.setAttribute('autocomplete', 'off');
    }
}

function addGuideLinks() {

    // Add user guide links to files view navigation pane...

    consoleDebug('addGuideLinks()');
    consoleDebug(window.location.pathname);

    if (window.location.pathname.includes('/s/NOT-FOR-PUBLICATION-')) {
        return;
    }

    let htmlFragment = `
        <div style="position: fixed; bottom: 0px; left: 15px; padding-bottom: 20px; padding-right: 15px;">
            <div style="padding-bottom: 20px;">
                <p>
                    <a style="color: #007FAD;" href="https://www.fairdata.fi/en/ida/quick-start-guide" rel="noopener" target="_blank">
                        IDA Quick Start Guide
                    </a>
                    <br>
                    <a style="color: #007FAD;" href="https://www.fairdata.fi/en/ida/user-guide" rel="noopener" target="_blank">
                        IDA User Guide
                    </a>
                </p>
            </div>
            <div>
                <p style="line-height: 120%">
                    Files can be added only in the Staging area (root folder ending in +)
                    <br>
                    <br>
                    Files are safely stored in the IDA service when they are in the Frozen area.
                    <br>
                    <br>
                    <a style="color: #007FAD;" href="https://www.fairdata.fi/en/ida/user-guide#project-data-storage" rel="noopener" target="_blank">
                        More information
                    </a>
                </p>
            </div>
        </div>
    `;

    const lang = getLanguageCode();

    if (lang === 'fi') {
        htmlFragment = `
            <div style="position: fixed; bottom: 0px; left: 15px; padding-bottom: 20px; padding-right: 15px;">
                <div style="padding-bottom: 20px;">
                    <p>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/idan-pikaopas" rel="noopener" target="_blank">
                            IDAn pikaopas
                        </a>
                        <br>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/kayttoopas" rel="noopener" target="_blank">
                            IDAn käyttöopas
                        </a>
                    </p>
                </div>
                <div>
                    <p style="line-height: 120%">
                        Tiedostoja voidaan lisätä ainoastaan Valmistelualueelle (juurikansio jonka päätteenä on +)
                        <br>
                        <br>
                        Tiedostot ovat turvallisesti tallennettu IDA&#8209;palveluun, kun ne ovat jäädytetyllä alueella.
                        <br>
                        <br>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/kayttoopas/#tiedostoselailu" rel="noopener" target="_blank">
                            Lisätietoja
                        </a>
                    </p>
                </div>
            </div>
        `;
    }

    if (lang === 'sv') {
        htmlFragment = `
            <div style="position: fixed; bottom: 0px; left: 15px; padding-bottom: 20px; padding-right: 15px;">
                <div style="padding-bottom: 20px;">
                    <p>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/en/ida/quick-start-guide" rel="noopener" target="_blank">
                            IDA Quick Start Guide
                        </a>
                        <br>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/en/ida/user-guide" rel="noopener" target="_blank">
                            IDA User Guide
                        </a>
                    </p>
                </div>
                <div>
                    <p style="line-height: 120%">
                        Filer kan läggas till endast i mappar med plustecken (+, område för preparering)
                        <br>
                        <br>
                        Filerna är säkert lagrade i IDA-tjänsten när de är i det frysta området.
                        <br>
                        <br>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/en/ida/user-guide#project-data-storage" rel="noopener" target="_blank">
                            Läs mer
                        </a>
                    </p>
                </div>
            </div>
        `;
    }

    // Find the nav element with id 'app-navigation-vue' or 'app-navigation'

    const navElement = document.getElementById('app-navigation-vue') || document.getElementById('app-navigation');

    // Append the HTML fragment to the end of the nav element

    if (navElement) {
        navElement.insertAdjacentHTML('beforeend', htmlFragment);
    }

}

function addActionNotifications() {

    // Add notification icon links to view header if there are pending and/or failed actions

    consoleDebug('addActionNotifications()');
    consoleDebug(window.location.pathname);

    if (window.location.pathname.includes('/s/NOT-FOR-PUBLICATION-')) {
        return;
    }

    const hasPendingActions = getActions('pending').length > 0;
    const hasFailedActions = getActions('failed').length > 0;

    consoleDebug('hasPendingActions: ' + hasPendingActions);
    consoleDebug('hasFailedActions: ' + hasFailedActions);

    if (hasPendingActions || hasFailedActions) {

        consoleDebug('Adding action notification icons ...');

        const pendingIcon = renderSvgComponent(IconDotsHorizontalCircleOutline).replace('fill="currentColor"', 'fill="white"');
        const failedIcon = renderSvgComponent(IconAlertCircleOutline).replace('fill="currentColor"', 'fill="white"');

        const htmlFragment = `
            <div style="display: flex; flex-direction: row; gap: 30px; padding-right: 15px;">
                ${hasFailedActions ? `<a title="${t('ida', 'Failed Actions')}" href="/apps/ida/actions/failed">${failedIcon}</a>` : ''}
                ${hasPendingActions ? `<a title="${t('ida', 'Pending Actions')}" href="/apps/ida/actions/pending">${pendingIcon}</a>` : ''}
            </div>
        `;

        const headerElement = document.querySelector('.header-start');

        // Append the HTML fragment to the end of the left side header element

        if (headerElement) {
            headerElement.insertAdjacentHTML('beforeend', htmlFragment);
        }
    }
}

function addRootFolderLabels() {

    // Add frozen/staging labels and project titles in root view

    consoleDebug('addRootFolderLabels()');
    consoleDebug(window.location.pathname);

    if (window.location.pathname.includes('/s/NOT-FOR-PUBLICATION-')) {
        return;
    }

    let addingIDALabels = false;

    const isRootView = () => {
        const pathname = window.location.pathname;
        const params = new URLSearchParams(window.location.search);
        const dir = params.get('dir');
        const isRoot = pathname.endsWith('/apps/files/files') && (!dir || dir === '/');
        consoleDebug('window.location.pathname: ' + window.location.pathname);
        consoleDebug('params.get(dir): ' + dir);
        consoleDebug('isRoot: ' + isRoot);
        return isRoot;
    }

    const addIDALabels = () => {

        consoleDebug('addIDALabels()');

        if (addingIDALabels) return;

        addingIDALabels = true;

        if (isRootView()) {

            consoleDebug('Disconnecting observer ...');
            observer.disconnect();

            const elements = document.querySelectorAll('span.files-list__row-name-');

            elements.forEach(element => {
                // Avoid duplicate processing on elements
                if (!element.hasAttribute('ida-labels-added')) {
                    const folderName = element.textContent.trim();
                    const isStaging = folderName.endsWith(STAGING_FOLDER_SUFFIX);
                    const project = isStaging ? folderName.slice(0, -1) : folderName;
                    const areaSpan = document.createElement('span');
                    areaSpan.textContent = isStaging ? t('ida', 'Staging') : t('ida', 'Frozen');
                    areaSpan.setAttribute('style', 'width: 100px; padding-left: 10px;');
                    areaSpan.classList.add('ida-area-label');
                    const titleSpan = document.createElement('span');
                    titleSpan.textContent = getProjectTitle(project);
                    titleSpan.classList.add('ida-project-title');
                    element.insertAdjacentElement('afterend', areaSpan);
                    areaSpan.insertAdjacentElement('afterend', titleSpan);
                    element.setAttribute('style', 'width: 150px;');   // Fix width of folder name for justified layout
                    element.setAttribute('ida-labels-added', 'true'); // Mark as modified
                }
            });

            consoleDebug('Reconnecting observer ...');
            observer.observe(document.body, { childList: true, subtree: true });
        }

        addingIDALabels = false;
    };

    const observerCallback = (mutationsList) => {
        addIDALabels();
    };

    const observer = new MutationObserver(observerCallback);

    addIDALabels();

    observer.observe(document.body, { childList: true, subtree: true });
}

function addNodeDetails() {

    // Populate node details table in the file details tab view

    consoleDebug('addNodeDetails()');
    consoleDebug(window.location.pathname);

    if (window.location.pathname.includes('/s/NOT-FOR-PUBLICATION-')) {
        return;
    }

    let lastPathname = null;
    let insertingNodeDetails = false;

    const contentVue = document.getElementById('content-vue');

    if (!contentVue) return;

    const createTableFromDict = (dict) => {

        consoleDebug('createTableFromDict()');

        const table = document.createElement('table');
        if (dict.size !== null && dict.size !== undefined && Number.isInteger(dict.size)) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'Size') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            dataCell.textContent = dict.size;
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        if (dict.checksum) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'Checksum') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            dataCell.textContent = dict.checksum;
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        if (dict.modified) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'Modified') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            dataCell.textContent = localizeTimestamp(dict.modified);
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        if (dict.uploaded) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'Uploaded') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            dataCell.textContent = localizeTimestamp(dict.uploaded);
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        if (dict.frozen) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'Frozen') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            dataCell.textContent = localizeTimestamp(dict.frozen);
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        if (dict.pid) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'File ID') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            dataCell.textContent = dict.pid;
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        if (dict.action) {
            const row = document.createElement('tr');
            const headerCell = document.createElement('th');
            headerCell.textContent = t('ida', 'Action') + ':';
            row.appendChild(headerCell);
            const dataCell = document.createElement('td');
            const link = document.createElement('a');
            link.href = '/apps/ida/action/' + dict.action;
            link.textContent = dict.action;
            link.style.color = '#007FAD';
            dataCell.appendChild(link);
            row.appendChild(dataCell);
            table.appendChild(row);
        }

        table.style.borderCollapse = 'collapse';
        table.style.width = '100%';
        table.style.border = 'none';
        table.style.fontSize = 'smaller';
        table.cellpadding = '2';
        return table;
    }

    const insertNodeDetails = () => {

        consoleDebug('insertNodeDetails()');

        if (insertingNodeDetails) return;

        insertingNodeDetails = true;

        const appSidebar = contentVue.querySelector('#app-sidebar-vue');

        if (appSidebar) {
            const appSidebarHeader = appSidebar.querySelector('.app-sidebar-header');
            if (appSidebarHeader) {
                const mainName = appSidebarHeader.querySelector('.app-sidebar-header__mainname');
                if (mainName) {
                    const filename = mainName.textContent.trim();
                    if (filename) {
                        const urlParams = new URLSearchParams(window.location.search);
                        const dir = urlParams.get('dir');
                        if (dir) {
                            const pathname = dir + '/' + filename;
                            consoleDebug('Last node details pathname:    ' + lastPathname);
                            consoleDebug('Current node details pathname: ' + pathname);
                            if (pathname !== lastPathname) {
                                consoleDebug('Inserting node details ...');
                                consoleDebug('Disconnecting observer ...');
                                observer.disconnect();
                                lastPathname = pathname;
                                const existingDiv = appSidebarHeader.querySelector('#ida-node-details');
                                if (existingDiv) {
                                    existingDiv.remove();
                                }
                                const nodeDetails = getNodeDetails(pathname);
                                if (nodeDetails) {
                                    const table = createTableFromDict(nodeDetails);
                                    const newDiv = document.createElement('div');
                                    newDiv.id = 'ida-node-details';
                                    newDiv.style.marginLeft = '8px';
                                    newDiv.style.paddingBottom = '10px';
                                    newDiv.style.overflowX = 'auto';
                                    newDiv.style.width = '100%';
                                    newDiv.appendChild(table);
                                    appSidebarHeader.appendChild(newDiv);
                                }
                                consoleDebug('Node details inserted.');
                                consoleDebug('Reconnecting observer ...');
                                observer.observe(contentVue, { childList: true, subtree: true });
                            }
                        }
                    }
                }
            }
        }

        insertingNodeDetails = false;
    }

    document.body.addEventListener('click', (event) => {
        if (event.target.classList.contains('action-button__text')) {
            const targetOption = event.target.closest('[data-cy-files-list-row-action="details"]');
            if (targetOption) {
                insertNodeDetails();
            }
        }
    });

    const observerCallback = (mutationsList) => {
        insertNodeDetails();
    }

    const observer = new MutationObserver(observerCallback);

    observer.observe(contentVue, { childList: true, subtree: true });
}

function blockAll(event) {
    // Used by toggleDragAndDrop to block drag-and-drop in all locations except staging area
    event.preventDefault();
    event.stopPropagation();
}

function toggleDragAndDrop() {

    // Disable drag-and-drop in all locations except staging area, and (re)enable in staging if disabled

    consoleDebug('toggleDragAndDrop()');
    consoleDebug(window.location.pathname);

    if (!window.location.pathname.includes('/apps/files/files')) {
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const pathname = params.get('dir');

    consoleDebug('Relative directory pathname: ' + pathname);

    const notStaging = window.location.pathname.endsWith('/apps/files/files') || isFrozen(pathname);
    const element = document.getElementById('content-vue');

    if (notStaging) {

        consoleDebug('Not in staging');

        if (element) {

            consoleDebug('Disabling drag-and-drop');

            element.addEventListener('dragenter', blockAll, true);
            element.addEventListener('dragover', blockAll, true);
            element.addEventListener('drop', blockAll, true);
        }
    } else {

        consoleDebug('In staging');

        if (element) {

            consoleDebug('Enabling drag-and-drop');

            element.removeEventListener('dragenter', blockAll, true);
            element.removeEventListener('dragover', blockAll, true);
            element.removeEventListener('drop', blockAll, true);
        }
    }
}

function fixDragAndDrop() {
    consoleDebug('fixDragAndDrop()');
    toggleDragAndDrop();
    executeOnURLChange(toggleDragAndDrop);
}

function fixRootActionMenus() {

    // Remove freeze/unfreeze/delete options from file action menus in root view (fixes bug in Nextcloud)

    consoleDebug('fixRootActionMenus()');
    consoleDebug(window.location.pathname);

    if (window.location.pathname.endsWith('/apps/files/files')) {

        consoleDebug('Fixing root action menus ...');

        // Initial processing for existing elements on view load

        const query = '.files-list__row-action-ida-freeze, .files-list__row-action-ida-unfreeze, .files-list__row-action-ida-delete, .files-list__row-action-rename, .files-list__row-action-move-copy, .files-list__row-action-delete';

        hideElements(document.querySelectorAll(query));

        const observerCallback = (mutationsList) => {
            if (focusIsInForm()) return;
            if (window.location.pathname.endsWith('/apps/files/files')) {
                hideElements(document.querySelectorAll(query));
            }
        };

        const observer = new MutationObserver(observerCallback);

        observer.observe(document.body, { childList: true, subtree: true });

        consoleDebug('Root action menus fixed.');
    }
}

function fixPublicShareView() {

    // Hide undesired view elements in public share view

    consoleDebug('fixPublicShareView()');
    consoleDebug(window.location.pathname);

    if (window.location.pathname.includes('/s/NOT-FOR-PUBLICATION-')) {

        consoleDebug('Removing undesired elements from public share view ...');

        const query = '#public-page-menu, .note-to-recipient__heading, .files-list__row-action-ida-freeze, .files-list__row-action-ida-unfreeze, .files-list__row-action-ida-delete, .files-list__row-action-rename, .files-list__row-action-move-copy, .files-list__row-action-delete';

        hideElements(document.querySelectorAll(query));

        const observerCallback = (mutationsList) => {
            if (focusIsInForm()) return;
            if (window.location.pathname.includes('/s/NOT-FOR-PUBLICATION-')) {
                hideElements(document.querySelectorAll(query));
            }
        };

        const observer = new MutationObserver(observerCallback);

        observer.observe(document.body, { childList: true, subtree: true });

        consoleDebug('Public share view fixed.');
    }
}

function fixUnifiedSearch() {

    consoleDebug('fixUnifiedSearcy()');

    const applyUnifiedSearchFixes = () => {
        // Update guidance text for unified search
        consoleDebug('Updating search guidance text ...');
        const inputElement = document.querySelector('#unified-search .input-field__input');
        if (inputElement) {
            const text3 = t('ida', 'Enter search terms here...');
            inputElement.setAttribute('placeholder', text3);
            const labelElement = inputElement.closest('#unified-search').querySelector(`label[for="${inputElement.id}"]`);
            if (labelElement) {
                labelElement.textContent = text3;
                labelElement.style.display = 'none';
            }
        }
    };

    const unifiedSearch = document.querySelector('body#body-user header#header div.header-end div.header-menu.unified-search-menu');

    if (unifiedSearch) {
        consoleDebug('Adding unified search click listener ...');
        unifiedSearch.addEventListener('click', function(event) {
            applyUnifiedSearchFixes();
        });
    }
}

function fixPageContent() {

    consoleDebug('fixPageContent()');

    let fixingPageContents = false;

    const updatePageTexts = () => {

        consoleDebug('updatePageTexts()');

        if (fixingPageContents) return;

        fixingPageContents = true;

        consoleDebug('Disconnecting observer ...');
        observer.disconnect();

        // Rename top right corner "Settings" menu item to "Security"
        consoleDebug('Looking for root user settings menu label ...');
        const aElement = document.querySelector('header#header nav#user-menu div#header-menu-user-menu a#settings');
        if (aElement) {
            const imgElement = aElement.querySelector('img');
            if (imgElement) {
                consoleDebug('Updating root user settings menu icon ...');
                imgElement.src = '/apps/settings/img/password.svg';
            }
            const divElement = aElement.querySelector('div.list-item-content__name');
            if (divElement) {
                consoleDebug('Updating root user settings menu label ...');
                const text1 = t('ida', 'Security');
                divElement.textContent = text1;
            }
        }

        // Update guidance text in empty folder view and hide redundant New menu button
        consoleDebug('Looking for empty folder view guidance text ...');
        const pElement = document.querySelector('.empty-content__description');
        if (pElement) {
            consoleDebug('Updating empty folder view guidance text ...');
            let text2 = t('ida', 'Upload files or folders by using drag and drop or by using the New menu above');
            const params = new URLSearchParams(window.location.search);
            const pathname = params.get('dir');
            if (isFrozen(pathname)) {
                text2 = t('ida', 'Files can be added only in the Staging area (root folder ending in +)');
            }
            pElement.textContent = text2;
        }
        hideElements(document.querySelectorAll('.empty-content__action'));

        consoleDebug('Reconnecting observer ...');
        observer.observe(document.body, { childList: true, subtree: true });

        fixingPageContents = false;

        consoleDebug('All page fixes applied.');
    }

    const observerCallback = (mutationsList) => {
        updatePageTexts();
    };

    const observer = new MutationObserver(observerCallback);

    updatePageTexts();

    observer.observe(document.body, { childList: true, subtree: true });
}

function fixOptions() {

    consoleDebug('fixOptions()');

    let applyingOptionFixes = false;

    const hideDisallowedOptions = (elements) => {

        consoleDebug('hideDisallowedOptions()');

        // Hide disallowed options elements, returning true if any elements were hidden, else false
        const disallowedOptionLabels = [
            'Custom permissions', 'Mukautetut oikeudet', 'Anpassade behörigheter',
            'Hide download', ' Piilota lataus', 'Dölj hämtning',
            'Wipe device', 'Tyhjennä laite', 'Rensa enhet',
            'Allow filesystem access', 'Salli pääsy tiedostojärjestelmään', 'Tillåt åtkomst till filsystemet',
            'Show files in grid view', 'fi?', 'Visa filer i rutnätsvy',
        ];
        if (elements) {
            elements.forEach(element => {
                if (window.getComputedStyle(element).display !== 'none') {
                    const textContent = element.textContent.trim();
                    consoleDebug('Checking element text content: ' + textContent);
                    if (disallowedOptionLabels.includes(textContent)) {
                        consoleDebug('Hiding disallowed option: ' + textContent);
                        element.style.display = 'none';
                    }
                }
            });
        }
    };

    const applyOptionFixes = () => {

        consoleDebug('applyOptionFixes()');

        if (applyingOptionFixes) return;

        applyingOptionFixes = true;

        consoleDebug('Disconnecting observer ...');
        observer.disconnect();

        // Hide temporary share link options
        consoleDebug('Hiding temporary share link disallowed options ...');
        hideDisallowedOptions(document.querySelectorAll('#advancedSectionAccordionAdvanced section .checkbox-radio-switch'));

        // Hide disallowed share, session, and device settings menu options
        consoleDebug('Hiding settings disallowed options ...');
        hideDisallowedOptions(document.querySelectorAll('ul[role="menu"] li'));

        consoleDebug('Reconnecting observer ...');
        observer.observe(document.body, { childList: true, subtree: true });

        applyingOptionFixes = false;

        consoleDebug('All option fixes applied.');
    };

    const observerCallback = (mutationsList) => {
        if (focusIsInForm()) return;
        applyOptionFixes();
    };

    const observer = new MutationObserver(observerCallback);

    applyOptionFixes();

    observer.observe(document.body, { childList: true, subtree: true });
}

function openFileDetailsFromIDAActionLink() {

    // If we've navigated to a file directory view from an action file listing link,
    // scroll to the file element in the view and open the file details sidebar...
    // (monitor DOM changes until menus are built and details view button can be clicked)

    consoleDebug('openFileDetailsFromIDAActionLink()');

    const urlParams = new URLSearchParams(window.location.search);
    const filename = urlParams.get('ida-action-filename');

    if (!filename) {
        return;
    }

    let opened = false;

    const open = () => {
        consoleDebug('openFileDetailsFromIDAActionLink: try to open');
        if (opened) {
            observer.disconnect();
            return;
        }
        // <tr data-cy-files-list-row-fileid="1854129" data-cy-files-list-row-name="test01.dat" class="files-list__row">
        const fileRow = document.querySelector(`tr.files-list__row[data-cy-files-list-row-name="${filename}"]`);
        if (fileRow) {
            fileRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            const menuToggleButton = fileRow.querySelector('button.action-item__menutoggle');
            if (menuToggleButton) {
                menuToggleButton.click();
                // <div><li data-cy-files-list-row-action="details"><button role="menuitem" class="action-button">
                const menuDiv = fileRow.closest('table').nextElementSibling;
                if (menuDiv) {
                    const detailsButton = menuDiv.querySelector('li[data-cy-files-list-row-action="details"] button[role="menuitem"].action-button');
                    if (detailsButton) {
                        detailsButton.click();
                        opened = true;
                        observer.disconnect(); // Only open once
                        consoleDebug('openFileDetailsFromIDAActionLink: opened');
                    }
                }
            }
        }
    }

    const observerCallback = (mutationsList) => {
        open();
    };

    const observer = new MutationObserver(observerCallback);

    open();

    observer.observe(document.body, { childList: true, subtree: true });

    setTimeout(() => {
        // If file not found and opened, and the page contains any other file list rows, assume
        // that the file is no longer present at that location and show an error message
        if (!opened) {
            consoleDebug('openFileDetailsFromIDAActionLink: timeout');
            observer.disconnect();
            const anyFileRow = document.querySelector('tr.files-list__row');
            if (anyFileRow) {
                showError(t('ida', 'File no longer frozen at this location') + ': ' + filename);
            }
        }
    }, 3000); // Observes for 3 seconds max
}

document.addEventListener('DOMContentLoaded', function() {

    consoleDebug('Fixing UI after page load ...');

    // If login page, fix and do nothing further
    if (window.location.pathname.endsWith('/login')) {
        fixLoginPage();
        return;
    }

    // Listen for changes in the URL in the browser address bar and force reload when
    // the page URL changes (fixes a bug in Nextcloud where using back/forward buttons
    // do not reload the page even though the URL changes)
    window.addEventListener('popstate', function() {
        location.reload();
    });

    // If user is admin, do nothing further
    const currentUser = getCurrentUser();
    if (currentUser && currentUser.isAdmin) {
        return;
    }

    // This (amazingly) disables the password confirmation dialog in Nextcloud, e.g.
    // when creating a new application password. Good thing we have extremely tight
    // CSRF protection in place.
    window.backendAllowsPasswordConfirmation = false;

    // Apply all other programmatic changes to the UI
    addGuideLinks();
    addActionNotifications();
    addRootFolderLabels();
    addNodeDetails();
    fixPublicShareView();
    fixRootActionMenus();
    fixDragAndDrop();
    fixUnifiedSearch();
    fixPageContent();
    fixOptions();
    openFileDetailsFromIDAActionLink();
});
