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

import { FileAction, registerFileAction } from '@nextcloud/files'
import '@nextcloud/dialogs/style.css'
import IconSnowflake from 'vue-material-design-icons/Snowflake.vue'
import IconSnowflakeMelt from 'vue-material-design-icons/SnowflakeMelt.vue'
import IconSnowflakeOff from 'vue-material-design-icons/SnowflakeOff.vue'
import { t } from '@nextcloud/l10n'
import { STAGING_FOLDER_SUFFIX } from './constants.js'
import { capitalize, renderSvgComponent, checkDatasets, checkScope, extractProjectName, getParentPathname, stripRootFolder } from './utils.js'

const modalOverlay = document.createElement('div');
const modalContainer = document.createElement('div');
const modalTitle = document.createElement('h3');
const modalContent = document.createElement('div');

modalOverlay.style.position = 'fixed';
modalOverlay.style.top = '0';
modalOverlay.style.left = '0';
modalOverlay.style.width = '100%';
modalOverlay.style.height = '100%';
modalOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
modalOverlay.style.zIndex = '9999';
modalOverlay.style.display = 'flex';
modalOverlay.style.justifyContent = 'center';
modalOverlay.style.alignItems = 'center';

modalContainer.style.backgroundColor = 'white';
modalContainer.style.padding = '20px';
modalContainer.style.borderRadius = '8px';
modalContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.2)';
modalContainer.style.width = '400px';
modalContainer.style.maxWidth = '90%';

modalTitle.style.margin = '0 0 10px 0';
modalTitle.style.fontSize = '18px';
modalTitle.style.textAlign = 'center';
modalTitle.style.width = '100%';

modalContent.style.marginBottom = '20px';

const buttonsContainer = document.createElement('div');
buttonsContainer.style.display = 'flex';
buttonsContainer.style.justifyContent = 'space-between';
buttonsContainer.style.marginTop = '20px';
buttonsContainer.style.width = '100%';

modalContainer.appendChild(modalTitle);
modalContainer.appendChild(modalContent);
modalContainer.appendChild(buttonsContainer);

modalOverlay.appendChild(modalContainer);

registerFileAction(new FileAction({
    id: 'ida-freeze',
    displayName: () => t('ida', 'Freeze'),
    iconSvgInline: () => renderSvgComponent(IconSnowflake),
    enabled: (files, view) => {
        return enableAction(files, view) === 2; // in staging area
    },
    exec: (node, view, dir) => {
        showActionDialog('freeze', node);
    },
}))

registerFileAction(new FileAction({
    id: 'ida-unfreeze',
    displayName: () => t('ida', 'Unfreeze'),
    iconSvgInline: () => renderSvgComponent(IconSnowflakeMelt),
    enabled: (files, view) => {
        return enableAction(files, view) === 1; // in frozen area
    },
    exec: (node, view, dir) => {
        showActionDialog('unfreeze', node);
    },
}))

registerFileAction(new FileAction({
    id: 'ida-delete',
    displayName: () => t('ida', 'Delete permanently'),
    iconSvgInline: () => renderSvgComponent(IconSnowflakeOff),
    enabled: (files, view) => {
        return enableAction(files, view) === 1; // in frozen area
    },
    exec: (node, view, dir) => {
        showActionDialog('delete', node);
    },
}))

function showActionDialog(action, node) {

    buttonsContainer.innerHTML = ''
    buttonsContainer.style.justifyContent = 'space-between';

    const cancelButton = document.createElement('button');
    const confirmButton = document.createElement('button');

    let title = capitalize(action) + ' ' + capitalize(node.type) + '?';
    const content = getDialogContent(title); // translated content returned
    title = t('ida', title);                 // translate title

    cancelButton.textContent = t('ida', 'Cancel');
    confirmButton.textContent = t('ida', capitalize(action));

    modalTitle.textContent = title;
    modalContent.innerHTML = content;

    cancelButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });

    confirmButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
        executeAction(action, node);
    });

    buttonsContainer.appendChild(cancelButton);
    buttonsContainer.appendChild(confirmButton);
    document.body.appendChild(modalOverlay);
}

function getDialogContent(title) {

    let content = '';

    switch (title) {

        case 'Freeze Folder?':
            content = content
                + t('ida', 'Are you sure you want to freeze all files within this folder, moving them to the frozen area and making them read-only?')
                + '<br/><br/>'
                + t('ida', 'Once frozen, the files will be visible in Qvain and may be included in one or more datasets.')
                + '<br/><br/>'
                + t('ida', 'The action cannot be terminated after it has been initiated.')
                + ' '
                + t('ida', 'Depending on the amount of data, the background operations may take several hours.')
                + ' '
                + t('ida', 'For more information, see the IDA User Quide.')
            break;

        case 'Freeze File?':
            content = content
                + t('ida', 'Are you sure you want to freeze this file, moving it to the frozen area and making it read-only?')
                + '<br/><br/>'
                + t('ida', 'Once frozen, the file will be visible in Qvain and may be included in one or more datasets.')
                + '<br/><br/>'
                + t('ida', 'The action cannot be terminated after it has been initiated.')
                + ' '
                + t('ida', 'Depending on the amount of data, the background operations may take several hours.')
                + ' '
                + t('ida', 'For more information, see the IDA User Quide.')
            break;

        case 'Unfreeze Folder?':
            content = content
                + t('ida', 'Are you sure you want to unfreeze all files within this folder, moving them back to the staging area and making them writable again?')
                + '<br/><br/>'
                + t('ida', 'Once unfrozen, the files will no longer be visible in Qvain, and any datasets which include any of the unfrozen files will become invalid and marked as deprecated.')
                + '<br/><br/>'
                + t('ida', 'The action cannot be terminated after it has been initiated.')
                + ' '
                + t('ida', 'Depending on the amount of data, the background operations may take several hours.')
                + ' '
                + t('ida', 'For more information, see the IDA User Quide.')
                + '<br/><br/><b style="color: red; display: block; text-align: center;">'
                + t('ida', 'THIS ACTION CANNOT BE UNDONE!')
                + '</b>';
            break;

        case 'Unfreeze File?':
            content = content
                + t('ida', 'Are you sure you want to unfreeze this file, moving it back to the staging area and making it writable again?')
                + '<br/><br/>'
                + t('ida', 'Once unfrozen, the file will no longer be visible in Qvain, and any datasets which include the unfrozen file will become invalid and marked as deprecated.')
                + '<br/><br/>'
                + t('ida', 'The action cannot be terminated after it has been initiated.')
                + ' '
                + t('ida', 'Depending on the amount of data, the background operations may take several hours.')
                + ' '
                + t('ida', 'For more information, see the IDA User Quide.')
                + '<br/><br/><b style="color: red; display: block; text-align: center;">'
                + t('ida', 'THIS ACTION CANNOT BE UNDONE!')
                + '</b>';
            break;

        case 'Delete Folder?':
            content = content
                + t('ida', 'Are you sure you want to permanently delete all files within this folder?')
                + '<br/><br/>'
                + t('ida', 'Once deleted, the files will no longer be visible in Qvain, and any datasets which include any of the deleted files will become invalid and marked as deprecated.')
                + '<br/><br/>'
                + t('ida', 'The action cannot be terminated after it has been initiated.')
                + ' '
                + t('ida', 'Depending on the amount of data, the background operations may take several hours.')
                + ' '
                + t('ida', 'For more information, see the IDA User Quide.')
                + '<br/><br/><b style="color: red; display: block; text-align: center;">'
                + t('ida', 'THIS ACTION CANNOT BE UNDONE!')
                + '</b>';
            break;

        case 'Delete File?':
            content = content
                + t('ida', 'Are you sure you want to permanently delete this file?')
                + '<br/><br/>'
                + t('ida', 'Once deleted, the file will no longer be visible in Qvain, and any datasets which include the deleted file will become invalid and marked as deprecated.')
                + '<br/><br/>'
                + t('ida', 'The action cannot be terminated after it has been initiated.')
                + ' '
                + t('ida', 'Depending on the amount of data, the background operations may take several hours.')
                + ' '
                + t('ida', 'For more information, see the IDA User Quide.')
                + '<br/><br/><b style="color: red; display: block; text-align: center;">'
                + t('ida', 'THIS ACTION CANNOT BE UNDONE!')
                + '</b>';
            break;

        default:
            console.warn('Unknown dialog title: ' + title);
    }

    return content;
}

function enableAction(files, view) {
    // Returns 0 if not in either frozen or staging area, returns 1 if in frozen area, and 2 if in staging area
    let result = 0; // assume at root
    // Note: the files array always has a single item, the file/node in question
    if (files && files.length > 0) {
        const pathname = files[0]._data.attributes.filename;
        if (pathname) {
            const segments = pathname.split('/');
            if (segments.length > 4) {
                const user = segments[2];
                if (user !== 'admin') {
                    result = 1 // either frozen or staging, but assume frozen
                    const rootDirectory = segments[3];
                    if (rootDirectory.endsWith(STAGING_FOLDER_SUFFIX)) {
                        result = 2; // in staging
                    }
                }
            }
        }
    }
    return result;
}

function executeAction(action, node, datasetsChecked = false) {
    try {
        const fullpath = node.path;
        const project = extractProjectName(fullpath);
        const pathname = stripRootFolder(fullpath);
        // Check for and disallow actions on root folders unless/until file actions are not based on entire view
        // and/or until bug where sublevel actions infect the root actions menu when view is updated without page
        // reload is resolved
        if (pathname === '/') {
            throw new Error(t('ida', 'Actions may not be performed on root project folders.'));
        }
        const nodeId = node.fileid;
        if (action === 'freeze' || datasetsChecked) {
            checkScope(project, pathname); // Will throw error if scope conflict
            const xhr = new XMLHttpRequest();
            const url = '/apps/ida/api/' + action;
            xhr.open('POST', url, false); // 'false' makes the request synchronous
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('IDA-Mode', 'GUI');
            const requestBody = JSON.stringify({ nextcloudNodeId: nodeId, project, pathname });
            xhr.send(requestBody);
            if (xhr.status >= 200 && xhr.status < 300) {
                handleActionSuccess(action, JSON.parse(xhr.responseText));
                return true;
            }
            // Try to parse the response JSON and extract and return the API error message
            let errorMessage = null;
            try {
                errorMessage = JSON.parse(xhr.responseText).message;
            } catch (error) {} // ignore
            if (errorMessage) {
                throw new Error(errorMessage);
            }
            throw new Error(`${xhr.status}: ${xhr.statusText}: ${xhr.responseText}`);
        } else {
            const affectedDatasets = checkDatasets(nodeId, project, pathname);
            const affectedDatasetsCount = affectedDatasets.length;
            if (affectedDatasetsCount > 0) {
                showDatasetDeprecationWarning(affectedDatasets, () => {
                    executeAction(action, node, true);
                });
                return true;
            } else {
                return executeAction(action, node, true);
            }
        }
    } catch (error) {
        handleActionError(action, error);
        return false;
    }
}

function handleActionSuccess(action, data) {

    buttonsContainer.innerHTML = ''
    buttonsContainer.style.justifyContent = 'space-between';

    const confirmButton = document.createElement('button');
    confirmButton.textContent = t('ida', 'OK');
    buttonsContainer.style.justifyContent = 'center';

    let targetUrl = '/';

    if (action === 'freeze') {

        modalTitle.textContent = t('ida', 'Action initiated successfully.');
        modalContent.innerHTML = t('ida', 'The data has been successfully frozen and moved to the project frozen area, located under the same relative pathname where it used to be located in the staging area.') + ' '
                                     + t('ida', 'Depending on the amount of data, the background operations may still take several hours.') + ' '
                                     + t('ida', 'The initiated action is') + ' '
                                     + '<a style="color: #007FAD;" href="/apps/ida/action/' + data.pid + '">' + data.pid + '</a>.';
        targetUrl = '/apps/files/?dir=' + encodeURIComponent('/' + data.project + getParentPathname(data.pathname));
        buttonsContainer.appendChild(confirmButton);

    } else if (action === 'unfreeze') {

        modalTitle.textContent = t('ida', 'Action initiated successfully.');
        modalContent.innerHTML = t('ida', 'The data has been successfully unfrozen and moved back to the project staging area, located under the same relative pathname where it used to be located in the frozen area.') + ' '
                                     + t('ida', 'Depending on the amount of data, the background operations may still take several hours.') + ' '
                                     + t('ida', 'The initiated action is') + ' '
                                     + '<a style="color: #007FAD;" href="/apps/ida/action/' + data.pid + '">' + data.pid + '</a>.';
        targetUrl = '/apps/files/?dir=' + encodeURIComponent('/' + data.project + '+' + getParentPathname(data.pathname));
        buttonsContainer.appendChild(confirmButton);

    } else if (action === 'delete') {

        modalTitle.textContent = t('ida', 'Action initiated successfully.');
        modalContent.innerHTML = t('ida', 'The data has been successfully deleted from the project frozen area.') + ' '
                                     + t('ida', 'Depending on the amount of data, the background operations may still take several hours.') + ' '
                                     + t('ida', 'The initiated action is') + ' '
                                     + '<a style="color: #007FAD;" href="/apps/ida/action/' + data.pid + '">' + data.pid + '</a>.';
        buttonsContainer.appendChild(confirmButton);
    }

    confirmButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
        window.location.reload();
    });

    document.body.appendChild(modalOverlay);
}

function handleActionError(action, error = null) {

    let message = null;

    if (error !== null) {
        try {
            if (typeof error === 'string') {
                error = JSON.parse(error);
            }
            if (typeof error === 'object') {
                if (error.message) {
                    message = error.message;
                } else if (error.details) {
                    message = error.details;
                } else if (error.error) {
                    message = error.error;
                }
            }
        } catch (e) {} // ignore

        if (!message) {
            if (typeof error === 'string') {
                message = error;
            } else if (typeof error === 'object') {
                try {
                    message = JSON.stringify(error);
                } catch (e) {} // ignore
            }
        }

        if (!message) {
            message = String(error);
        }
    }

    if (!message) {
        message = 'An unknown error occurred.';
    }

    message = t('ida', message);

    buttonsContainer.innerHTML = ''
    buttonsContainer.style.justifyContent = 'center';

    const cancelButton = document.createElement('button');

    cancelButton.textContent = t('ida', 'Close');

    modalTitle.textContent = t('ida', capitalize(action) + ' action failed');
    modalContent.innerHTML = t('ida', String(message)); // usually already translated, but we attempt translation anyway

    buttonsContainer.appendChild(cancelButton);

    cancelButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });

    document.body.appendChild(modalOverlay);
}

function showDatasetDeprecationWarning(affectedDatasets, proceedCallback) {

    buttonsContainer.innerHTML = ''
    buttonsContainer.style.justifyContent = 'space-between';

    const cancelButton = document.createElement('button');
    const confirmButton = document.createElement('button');

    cancelButton.textContent = t('ida', 'No');
    confirmButton.textContent = t('ida', 'Yes');

    modalTitle.textContent = t('ida', 'Warning: Datasets will be deprecated!');
    modalContent.innerHTML = '<b style="color: red">'
                                 + t('ida', 'One or more files included in the specified action belong to a dataset. Proceeding with the specified action will permanently deprecate the datasets listed below.') + ' '
                                 + '<br/><br/>'
                                 + t('ida', 'THIS ACTION CANNOT BE UNDONE!') + ' '
                                 + '</b><br/><br/>'
                                 + buildDatasetLinkListing(affectedDatasets) + ' '
                                 + '<br/><br/>'
                                 + t('ida', 'Do you wish to proceed?');

    cancelButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
    });

    confirmButton.addEventListener('click', () => {
        document.body.removeChild(modalOverlay);
        proceedCallback();
    });

    buttonsContainer.appendChild(cancelButton);
    buttonsContainer.appendChild(confirmButton);
    document.body.appendChild(modalOverlay);
}

function buildDatasetLinkListing(datasets) {
    const domain = window.location.hostname.substring(4);
    const count = datasets.length;
    let listing = '';
    let limit = count;
    if (count > 5) {
        limit = 5;
    }
    for (let i = 0; i < limit; i++) {
        const pid = datasets[i].pid;
        listing = listing
            + '<a style="color: #007FAD; padding-left: 20px;" href="https://etsin.'
            + domain
            + '/dataset/'
            + pid
            + '?preview=1" target="_blank">'
            + datasets[i].title
            + '</a><br>';
    }
    if (count > limit) {
        listing = listing + '<span style="color: gray; padding-left: 20px;">(' + (count - limit) + ' ' + t('ida', 'not shown') + ')</span><br>';
    }
    return listing;
}
