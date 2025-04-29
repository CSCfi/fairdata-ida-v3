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

import Vue from 'vue'
import { STAGING_FOLDER_SUFFIX } from './constants.js'

const CONSOLE_DEBUG = false;  // set to true to enable console.debug messages

export const consoleDebug = (...args) => {
    if (CONSOLE_DEBUG) {
        console.debug(...args);
    }
}

export const capitalize = (s) => {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

export const renderSvgComponent = (Component) => {
    const container = document.createElement('div');
    const app = new Vue({
        render: h => h(Component),
    });
    app.$mount(container);
    return app.$el.outerHTML;
}

export const getNodeDetails = (pathname) => {
    // Retrieves all metadata for a file, either in staging or frozen, via the IDA API inventory
    // endpoint. Will return empty array if pathname corresponds to folder, resulting in no
    // details table being generated in the file details pane. No need to check whether file
    // or folder, which would just be an additional API call.
    if (pathname == null || pathname === '') {
        return null;
    }
    try {
        consoleDebug('Fetching node details for ' + pathname + ' ...');
        const project = extractProjectName(pathname);
        const xhr = new XMLHttpRequest();
        const url = '/apps/ida/api/inventory/file/' + project + '?pathname=' + encodeURIComponent(pathname);
        xhr.open('GET', url, false); // 'false' makes the request synchronous
        xhr.setRequestHeader('IDA-Mode', 'GUI');
        xhr.send();
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            consoleDebug('Node details retrieved for ' + pathname + ' successfully.');
            return data;
        }
        if (xhr.status === 404) {
            consoleDebug('Node details for ' + pathname + ' not found.');
            return null;
        }
        throw new Error(`${xhr.status}: ${xhr.statusText}: ${xhr.responseText}`);
    } catch (error) {
        console.warn(t('ida', 'Error fetching file details') + ': pathname: ' + pathname + ': ', error);
        return null; // Always return null on error, no matter what...
    }
}

export const getProjectTitle = (project) => {
    if (project == null || project === '') {
        return null;
    }
    try {
        const xhr = new XMLHttpRequest();
        const url = '/apps/ida/api/getProjectTitle?project=' + encodeURIComponent(project);
        xhr.open('GET', url, false); // 'false' makes the request synchronous
        xhr.setRequestHeader('IDA-Mode', 'GUI');
        xhr.send();
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            return data.message; // Return project title
        }
        throw new Error(`${xhr.status}: ${xhr.statusText}`);
    } catch (error) {
        console.warn(t('ida', 'Error fetching project title') + ': ', error);
        return project; // Always return project name as default title, no matter what...
    }
}

export const getActions = (status = 'pending') => {
    try {
        const xhr = new XMLHttpRequest();
        const url = '/apps/ida/api/actions?status=' + status;
        xhr.open('GET', url, false); // 'false' makes the request synchronous
        xhr.setRequestHeader('IDA-Mode', 'GUI');
        xhr.send();
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            return data;
        }
        throw new Error(`${xhr.status}: ${xhr.statusText}`);
    } catch (error) {
        console.warn(t('ida', 'Error fetching pending actions') + ': ', error);
        return []; // Always return empty list, no matter what...
    }
}

export const checkScope = (project, scope) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/apps/ida/api/scopeOK', false); // 'false' makes it synchronous
    xhr.setRequestHeader('IDA-Mode', 'GUI');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify({ project: project, pathname: scope }));
    if (xhr.status === 200) {
        return true; // Indicates no conflict
    }
    // Try to parse the response JSON and extract and return the API error message
    try {
        const responseJson = JSON.parse(xhr.responseText);
        const errorMessage = responseJson.message;
        if (errorMessage) {
            throw new Error(errorMessage);
        }
    } catch (error) {} // ignore
    throw new Error(`${xhr.status}: ${xhr.statusText}: ${xhr.responseText}`);
}

export const checkDatasets = (nodeId, project, pathname) => {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/apps/ida/api/datasets', false); // 'false' makes the request synchronous
        xhr.setRequestHeader('IDA-Mode', 'GUI');
        xhr.setRequestHeader('Content-Type', 'application/json');
        const requestBody = JSON.stringify({
            nextcloudNodeId: nodeId,
            project: project,
            pathname: pathname,
        });
        xhr.send(requestBody);
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            return data;
        }
        throw new Error(`${xhr.status}: ${xhr.statusText}: ${xhr.responseText}`);
    } catch (error) {
        throw new Error(t('Failed to check dataset intersection') + ': ' + error);
    }
}

export const extractProjectName = (pathname) => {
    const matches = pathname.match('^/[^/][^/]*');
    if (matches != null && matches.length > 0) {
        const project = matches[0];
        if (project.endsWith(STAGING_FOLDER_SUFFIX)) {
            return project.substr(1, project.length - 2);
        } else {
            return project.substr(1);
        }
    }
    return null;
}

export const getParentPathname = (pathname) => {
    const matches = pathname.match('/[^/][^/]*$');
    if (matches != null && matches.length > 0) {
        return pathname.substr(0, pathname.length - matches[0].length);
    }
    return pathname;
}

export const stripRootFolder = (pathname) => {
    if (isRootProjectFolder(pathname)) {
        return '/';
    }
    const matches = pathname.match('^/[^/][^/]*/');
    if (matches != null && matches.length > 0) {
        return pathname.substr(matches[0].length - 1);
    }
    return pathname;
}

export const extractBasename = (pathname) => {
    const matches = pathname.match('[^/][^/]*$');
    if (matches != null && matches.length > 0) {
        return matches[0];
    }
    return pathname;
}

export const isRootProjectFolder = (pathname) => {
    return pathname.search('^/[^/][^/]*$') >= 0;
}

export const isFrozen = (pathname) => {
    if (pathname == null || pathname === '') {
        return false;
    }
    const project = extractProjectName(pathname);
    if (project == null || project === '') {
        return false;
    }
    return ((pathname === '/' + project) || (pathname.startsWith('/' + project + '/')));
}

export const localizeTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const locale = window.navigator.userLanguage || window.navigator.language;
    const opts = {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        seconds: '2-digit',
        timeZone: 'UTC',
    };
    return date.toLocaleTimeString(locale, opts) + ' UTC';
}

export const hideElements = (elements) => {
    if (elements) {
        elements.forEach(element => {
            element.style.setProperty('display', 'none', 'important');
        });
    }
}
