/*
 * This file is part of the Fairdata IDA research data storage service.
 *
 * Copyright (C) 2024 Ministry of Education and Culture, Finland
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
import { renderSvgComponent, getProjectTitle, getNodeDetails, getActions, localizeTimestamp, hideElements, isFrozen } from './utils.js'

function getLanguageCode() {
    return (navigator.language || navigator.userLanguage || 'en').split('-')[0];
}

function focusIsInForm() {
    const inForm = document.activeElement.matches('input, textarea, select, [contenteditable=true]');
    if (inForm) console.debug('User focus in in a form');
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

/*
function hideUnwantedElements() {

    // CLEANUP ? (does not appear to be needed any longer after refactoring of CSS)

    // This function is redundant with CSS defined in the IDA theme stylesheet server.css, but
    // is required for older browsers that do not apply the CSS rules reliably, even though the
    // rules are intended to be maximally portable. The CSS rules are applied more quickly in
    // modern browsers, ensuring the unwanted elements are hidden as soon as possible; but this
    // function is still needed to ensure the elements are hidden even in older browsers.

    const selectors = [
        '#body-public > footer > p.footer__simple-sign-up',
        '.unified-search-modal__filters .action-item:nth-child(1)',
        '.unified-search-modal__filters .v-popper:nth-child(3)',
        '.sharingTabDetailsView__quick-permissions',
        '.sharing-entry .share-select',
        'li.action button > span.qrcode-icon',
        'div.app-files li.files-list__row-action-edit-locally',
        'div.app-files li.app-navigation-entry-wrapper.files-navigation__item[data-cy-files-navigation-item=\'personal\']',
        'div.app-files li.app-navigation-entry-wrapper.files-navigation__item[data-cy-files-navigation-item=\'folders\']',
        'div.app-files li.app-navigation-entry-wrapper.files-navigation__item[data-cy-files-navigation-item=\'shareoverview\'] > div > button.icon-collapse',
        'div.app-files .app-navigation-entry__settings',
        'div.app-files button.files-list__header-grid-button',
        'div.app-files div.file-list-filter-type',
        'div.app-files div.file-list-filter-accounts',
        'div.app-files div.sharingTab__content > *:not(.sharing-link-list)',
        'form.login-form > a#lost-password',
        '#body-settings nav.app-navigation-personal li[data-section-id=\'personal-info\']',
        '#body-settings nav.app-navigation-personal li[data-section-id=\'sharing\']',
        '#body-settings nav.app-navigation-personal li[data-section-id=\'theming\']',
        '#body-settings nav.app-navigation-personal li[data-section-id=\'availability\']',
        '#body-settings nav.app-navigation-personal li[data-section-id=\'workflow\']',
        '#user-menu #accessibility_settings',
        '#app-sidebar-vue p.app-sidebar-header__subname',
        '#app-content[data-active-section-id=\'security\'] div.settings-section:not(#security)',
        '#app-content[data-active-section-id=\'security\'] div.section:not(#security)',
        '.action-item__popper .upload-picker__menu-entry[data-cy-upload-picker-menu-entry=\'file-request\']',
        'div.token-dialog__qrcode',
        '#contactsmenu',
        '#ida-local-login #lost-password',
        '#ida-local-login #alternative-logins',
        '#ida-local-login a',
    ];

    selectors.forEach(selector => {
        try {
            hideElements(document.querySelectorAll(selector));
        } catch (error) {}
    });
}
*/

function addGuideLinks() {

    // Add user guide links to files view navigation pane...

    let htmlFragment = `
        <div style="position: fixed; bottom: 20px; left: 20px;">
            <div style="padding-top: 0px; padding-bottom: 20px;">
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
            <div style="width: 250px; padding-right: 25px; padding-top: 0px; padding-bottom: 74px;">
                <p style="padding: 7px; border: 1px; border-style:solid; border-color:#555; color:#555; line-height: 120%">
                    <b>Note:</b> Files are safely stored in the IDA service when they are in the Frozen area.
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
            <div style="position: fixed; bottom: 20px; left: 20px;">
                <div style="padding-top: 0px; padding-bottom: 20px;">
                    <p>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/idan-pikaopas" rel="noopener" target="_blank">
                            IDAn pikaopas
                        </a>
                        <br>
                        <a style="color: #007FAD;" href="https://www.fairdata.fi/kayttoopas" rel="noopener" target="_blank">
                            IDAn käyttäjänopas
                        </a>
                    </p>
                </div>
                <div style="width: 250px; padding-right: 25px; padding-top: 0px; padding-bottom: 74px;">
                    <p style="padding: 7px; border: 1px; border-style:solid; border-color:#555; color:#555; line-height: 120%">
                        <b>Huom:</b> Tiedostot ovat turvallisesti tallennettu IDA&#8209;palveluun, kun ne ovat jäädytetyllä alueella.
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
            <div style="position: fixed; bottom: 20px; left: 20px;">
                <div style="padding-top: 0px; padding-bottom: 20px;">
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
                <div style="width: 250px; padding-right: 25px; padding-top: 0px; padding-bottom: 74px;">
                    <p style="padding: 7px; border: 1px; border-style:solid; border-color:#555; color:#555; line-height: 120%">
                        <b>Notera:</b> Filerna är säkert lagrade i IDA-tjänsten när de är i det frysta området.
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

    const hasPendingActions = getActions('pending').length > 0;
    const hasFailedActions = getActions('failed').length > 0;
    // TODO add suspended project notification

    if (hasPendingActions || hasFailedActions) {

        const pendingIcon = renderSvgComponent(IconDotsHorizontalCircleOutline).replace('fill="currentColor"', 'fill="white"');
        const alertIcon = renderSvgComponent(IconAlertCircleOutline).replace('fill="currentColor"', 'fill="white"');

        const htmlFragment = `
            <div style="display: flex; flex-direction: row; gap: 30px; padding-right: 15px;">
                ${hasFailedActions ? `<a title="${t('ida', 'Failed Actions')}" href="/apps/ida/actions/failed">${alertIcon}</a>` : ''}
                ${hasPendingActions ? `<a title="${t('ida', 'Pending Actions')}" href="/apps/ida/actions/pending">${pendingIcon}</a>` : ''}
            </div>
        `;

        // Find the nav element with id 'app-navigation-vue' or 'app-navigation'

        const headerElement = document.querySelector('.header-left');

        // Append the HTML fragment to the end of the left side header element

        if (headerElement) {
            headerElement.insertAdjacentHTML('beforeend', htmlFragment);
        }
    }
}

function addRootFolderLabels() {

    // Add frozen/staging labels and project titles in root view

    if (window.location.pathname.endsWith('/apps/files/files')) {

        const addIDALabels = (elements) => {

            observer.disconnect();

            elements.forEach(element => {

                // Avoid duplicate processing

                if (!element.hasAttribute('ida-labels-added')) {
                    const folderName = element.textContent.trim();
                    const isStaging = folderName.endsWith(STAGING_FOLDER_SUFFIX);
                    const project = isStaging ? folderName.slice(0, -1) : folderName;
                    const areaSpan = document.createElement('span');
                    areaSpan.textContent = isStaging ? t('ida', 'Staging') : t('ida', 'Frozen');
                    areaSpan.setAttribute('style', 'width: 100px;');
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

            observer.observe(document.body, { childList: true, subtree: true });
        };

        const observerCallback = (mutationsList) => {
            if (window.location.pathname.endsWith('/apps/files/files')) {
                const elements = document.querySelectorAll('span.files-list__row-name-');
                addIDALabels(elements);
            }
        };

        const observer = new MutationObserver(observerCallback);

        const elements = document.querySelectorAll('span.files-list__row-name-');
        addIDALabels(elements);

        observer.observe(document.body, { childList: true, subtree: true });
    }
}

function addNodeDetails() {

    let lastPathname = null;

    let insertingNodeDetails = false;

    const createTableFromDict = (dict) => {
        const table = document.createElement('table');
        if (dict.size) {
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
        table.cellPadding = '2';
        return table;
    }

    const insertNodeDetails = () => {

        if (insertingNodeDetails) return;

        insertingNodeDetails = true;

        const appSidebar = document.getElementById('app-sidebar-vue');
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
                            console.debug('Inserting node details ...');
                            const pathname = dir + '/' + filename;
                            console.debug('Last pathname:    ' + lastPathname);
                            console.debug('Current pathname: ' + pathname);
                            if (pathname !== lastPathname) {
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
                                    newDiv.setAttribute('style', 'margin-left: 8px;');
                                    newDiv.style.overflowX = 'auto';
                                    newDiv.style.width = '100%';
                                    newDiv.appendChild(table);
                                    appSidebarHeader.appendChild(newDiv);
                                }
                                observer.observe(document.body, { childList: true, subtree: true });
                                console.debug('Node details inserted.');
                            } else {
                                console.debug('Node details unchanged.');
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

    const observer = new MutationObserver(() => {
        insertNodeDetails();
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

function blockAll(event) {
    // Used by toggleDragAndDrop to block drag-and-drop in all locations except staging area
    event.preventDefault();
    event.stopPropagation();
}

function toggleDragAndDrop() {

    // Disable drag-and-drop in all locations except staging area, and (re)enable in staging if disabled

    console.debug(window.location.pathname);

    if (!window.location.pathname.includes('/apps/files/files')) {
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const pathname = params.get('dir');

    console.debug('Relative directory pathname: ' + pathname);

    const notStaging = window.location.pathname.endsWith('/apps/files/files') || isFrozen(pathname);
    const element = document.getElementById('content-vue');

    if (notStaging) {

        console.debug('Not in staging');

        if (element) {

            console.debug('Disabling drag-and-drop');

            element.addEventListener('dragenter', blockAll, true);
            element.addEventListener('dragover', blockAll, true);
            element.addEventListener('drop', blockAll, true);
        }
    } else {

        console.debug('In staging');

        if (element) {

            console.debug('Enabling drag-and-drop');

            element.removeEventListener('dragenter', blockAll, true);
            element.removeEventListener('dragover', blockAll, true);
            element.removeEventListener('drop', blockAll, true);
        }
    }
}

function fixDragAndDrop() {
    toggleDragAndDrop();
    executeOnURLChange(toggleDragAndDrop);
}

function fixPageContent() {

    const text1 = t('ida', 'Files can be added only in the Staging area (root folder ending in +)');
    const text2 = t('ida', 'Upload files or folders by using drag and drop or by using the New menu above');
    const text3 = t('ida', 'Enter search terms here...');

    let applyingFixes = false;

    const hideDisallowedOptions = (elements) => {

        const disallowedOptionLabels = [
            'Custom permissions', 'Mukautetut oikeudet', 'Anpassade behörigheter',
            'Hide download', ' Piilota lataus', 'Dölj hämtning',
            'Wipe device', 'Tyhjennä laite', 'Rensa enhet',
            'Allow filesystem access', 'Salli pääsy tiedostojärjestelmään', 'Tillåt åtkomst till filsystemet',
        ];

        if (elements) {
            elements.forEach(element => {
                if (window.getComputedStyle(element).display !== 'none') {
                    if (disallowedOptionLabels.includes(element.textContent.trim())) {
                        element.style.display = 'none';
                    }
                }
            });
        }
    };

    const applyFixes = () => {

        console.debug('Applying UI fixes ...');

        if (applyingFixes) {
            console.debug('UI fixes already in progress ...');
            return;
        }

        applyingFixes = true;

        console.debug('Disconnecting observer ...');
        observer.disconnect();

        // Update guidance text of disabled New menu button
        console.debug('Updating New menu button guidance text ...');
        const buttonElement = document.querySelector('.files-list__header-upload-button--disabled');
        if (buttonElement) {
            buttonElement.setAttribute('aria-label', text1);
            buttonElement.setAttribute('title', text1);
        }

        // Update guidance text in empty folder view and hide redundant New menu button
        console.debug('Updating empty folder view guidance text ...');
        const pElement = document.querySelector('.empty-content__description');
        if (pElement) {
            pElement.textContent = text2;
        }
        hideElements(document.querySelectorAll('.empty-content__action'));

        // Update guidance text for unified search
        console.debug('Updating search guidance text ...');
        const inputElement = document.querySelector('#unified-search .input-field__input');
        if (inputElement) {
            inputElement.setAttribute('placeholder', text3);
            const labelElement = inputElement.closest('#unified-search').querySelector(`label[for="${inputElement.id}"]`);
            if (labelElement) {
                labelElement.textContent = text3;
                labelElement.style.display = 'none';
            }
        }

        // Hide temporary share link options
        console.debug('Hiding temporary share link disallowed options ...');
        hideDisallowedOptions(document.querySelectorAll('#advancedSectionAccordionAdvanced span.checkbox-radio-switch.checkbox-radio-switch-checkbox'));

        // Hide disallowed share, session, and device settings menu options
        console.debug('Hiding settings disallowed options ...');
        hideDisallowedOptions(document.querySelectorAll('ul[role="menu"] li'));

        applyingFixes = false;

        console.debug('Reconnecting observer ...');
        observer.observe(document.body, { childList: true, subtree: true });

        console.debug('UI fixes applied.');
    };

    const unifiedSearch = document.querySelector('body#body-user header#header div.header-right div.header-menu.unified-search-menu');

    if (unifiedSearch) {
        unifiedSearch.addEventListener('click', function(event) {
            applyFixes();
        });
    }

    const observerCallback = (mutationsList) => {
        if (focusIsInForm()) return;
        applyFixes();
    };

    const observer = new MutationObserver(observerCallback);

    applyFixes();

    observer.observe(document.body, { childList: true, subtree: true });
}

function fixRootActionMenus() {

    // Remove freeze/unfreeze/delete options from file action menus in root view (fixes bug in Nextcloud)

    if (window.location.pathname.endsWith('/apps/files/files')) {

        console.debug('Fixing root action menus ...');

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

        console.debug('Root action menus fixed.');
    }
}

function openFileDetailsFromIDAActionLink() {

    // If we've navigated to a file directory view from an action file listing link,
    // scroll to the file element in the view and open the file details sidebar...
    // (monitor DOM changes until menus are built and details view button can be clicked)

    const urlParams = new URLSearchParams(window.location.search);
    const filename = urlParams.get('ida-action-filename');

    if (!filename) {
        return;
    }

    let opened = false;

    const open = () => {
        console.debug('openFileDetailsFromIDAActionLink: try to open');
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
                        console.debug('openFileDetailsFromIDAActionLink: opened');
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
            console.debug('openFileDetailsFromIDAActionLink: timeout');
            observer.disconnect();
            const anyFileRow = document.querySelector('tr.files-list__row');
            if (anyFileRow) {
                showError(t('ida', 'File no longer frozen at this location') + ': ' + filename);
            }
        }
    }, 3000); // Observes for 3 seconds max
}

document.addEventListener('DOMContentLoaded', function() {

    console.debug('Fixing UI after page load ...');

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
    fixDragAndDrop();
    fixRootActionMenus();
    fixPageContent();
    openFileDetailsFromIDAActionLink();
});
