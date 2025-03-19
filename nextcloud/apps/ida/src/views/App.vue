<!--
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
-->
<template>
    <NcContent app-name="ida">
        <NcAppNavigation>
            <template #list>
                <NcAppNavigationItem :name="t('ida', 'Pending')" :active="currentStatus === 'pending'"
                    @click="openActionListing('pending')">
                    <template #icon>
                        <IconDotsHorizontalCircleOutline :size="20" />
                    </template>
                </NcAppNavigationItem>
                <NcAppNavigationItem :name="t('ida', 'Completed')" :active="currentStatus === 'completed'"
                    @click="openActionListing('completed')">
                    <template #icon>
                        <IconCheckCircleOutline :size="20" />
                    </template>
                </NcAppNavigationItem>
                <NcAppNavigationItem :name="t('ida', 'Failed')" :active="currentStatus === 'failed'"
                    @click="openActionListing('failed')">
                    <template #icon>
                        <IconAlertCircleOutline :size="20" />
                    </template>
                </NcAppNavigationItem>
                <NcAppNavigationItem :name="t('ida', 'Cleared')" :active="currentStatus === 'cleared'"
                    @click="openActionListing('cleared')">
                    <template #icon>
                        <IconCloseCircleOutline :size="20" />
                    </template>
                </NcAppNavigationItem>
            </template>
        </NcAppNavigation>
        <NcAppContent>
            <template>
                <div class="main-content">
                    <div v-if="currentAction.pid">
                        <!-- Detailed Action View -->
                        <div class="ida-heading">Action:</div>
                        <div class="ida-table-wrapper">
                            <table class="action-details ida-table">
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.initiated }" class="ida-wide-cell">
                                        {{ t('ida', 'Initiated') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width">
                                        {{ currentAction.initiated }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.pid }" class="ida-wide-cell">
                                        {{ t('ida', 'Action ID') }}
                                    </th>
                                    <td class="fixed-width">
                                        {{ currentAction.pid }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.pids }" class="ida-wide-cell">
                                        {{ t('ida', 'File IDs Generated') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width">
                                        {{ currentAction.pids }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.action }" class="ida-wide-cell">
                                        {{ t('ida', 'Action') }}
                                    </th>
                                    <td>
                                        {{ t('ida', capitalize(currentAction.action)) }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.storage }" class="ida-wide-cell">
                                        {{ t('ida', 'File Storage Updated') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width">
                                        {{ currentAction.storage }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.project }" class="ida-wide-cell">
                                        {{ t('ida', 'Project') }}
                                    </th>
                                    <td>
                                        {{ currentAction.project }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.checksums }" class="ida-wide-cell">
                                        {{ t('ida', 'File Checksums Generated') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width">
                                        {{ currentAction.checksums }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.user }" class="ida-wide-cell">
                                        {{ t('ida', 'User') }}
                                    </th>
                                    <td>
                                        {{ currentAction.user }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.metadata }" class="ida-wide-cell">
                                        {{ t('ida', 'File Metadata Stored') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width">
                                        {{ currentAction.metadata }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.pathname }" class="ida-wide-cell">
                                        {{ t('ida', 'Scope') }}
                                    </th>
                                    <td class="fixed-width">
                                        {{ currentAction.pathname }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.replication }" class="ida-wide-cell">
                                        {{ t('ida', 'Files Replicated') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width">
                                        {{ currentAction.replication }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.nodetype }" class="ida-wide-cell">
                                        {{ t('ida', 'Node Type') }}
                                    </th>
                                    <td>
                                        {{ t('ida', capitalize(currentAction.nodetype)) }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.completed }" class="ida-wide-cell">
                                        {{ t('ida', 'Completed') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width" style="color: green; font-weight: bold;">
                                        {{ currentAction.completed }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.filecount }" class="ida-wide-cell">
                                        {{ t('ida', 'File Count') }}
                                    </th>
                                    <td class="fixed-width">
                                        {{ currentAction.filecount }}
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.failed }" class="ida-wide-cell">
                                        {{ t('ida', 'Failed') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width" style="color: red; font-weight: bold;">
                                        {{ currentAction.failed }}
                                    </td>
                                    <th :class="{ 'gray-text': !(currentAction.retry || (currentAction.failed && !currentAction.cleared)) }" class="ida-wide-cell">
                                        {{ t('ida', 'Retried by') }}
                                    </th>
                                    <td class="fixed-width ida-link" v-if="currentAction.retry"
                                        @click="openActionDetails(currentAction.retry)">
                                        {{ currentAction.retry }}
                                    </td>
                                    <td class="fixed-width ida-link" v-else-if="currentAction.failed && !currentAction.cleared"
                                        @click="retryAction(currentAction.pid)">
                                        {{ t('ida', 'RETRY') }}
                                    </td>
                                    <td v-else>
                                        &nbsp;
                                    </td>
                                </tr>
                                <tr>
                                    <th :class="{ 'gray-text': !currentAction.cleared }" class="ida-wide-cell">
                                        {{ t('ida', 'Cleared') }}
                                    </th>
                                    <td class="ida-wide-cell fixed-width" style="color: orange; font-weight: bold;">
                                        {{ currentAction.cleared }}
                                    </td>
                                    <th :class="{ 'gray-text': !currentAction.retrying }" class="ida-wide-cell">
                                        {{ t('ida', 'Retry of') }}
                                    </th>
                                    <td class="fixed-width ida-link" v-if="currentAction.retrying"
                                        @click="openActionDetails(currentAction.retrying)">
                                        {{ currentAction.retrying }}
                                    </td>
                                    <td v-else>
                                        &nbsp;
                                    </td>
                                </tr>
                            </table>
                            <div style="padding-top: 30px; background-color: white;">
                                <div v-if="currentActionFiles.length > 0" class="ida-table-wrapper">
                                    <table id="action-files" class="ida-table" :style="{ pointerEvents: currentAction.action === 'delete' ? 'none' : 'auto' }">
                                        <thead>
                                            <tr>
                                                <th class="ida-wide-cell">
                                                    {{ t('ida', 'File ID') }}
                                                </th>
                                                <th>
                                                    {{ t('ida', 'Pathname') }}
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr v-for="file in currentActionFiles" :key="file.pid">
                                                <template v-if="file.url">
                                                    <td class="ida-fixed">
                                                        <a :href="file.url">{{ file.pid }}</a>
                                                    </td>
                                                    <td class="ida-fixed">
                                                        <a :href="file.url">{{ file.pathname }}</a>
                                                    </td>
                                                </template>
                                                <template v-else>
                                                    <td class="ida-fixed">{{ file.pid }}</td>
                                                    <td class="ida-fixed">{{ file.pathname }}</td>
                                                </template>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <div v-if="currentActionFiles.length >= maxFileCount" style="padding-top: 10px;">
                                        <p>
                                            {{ t('ida', '... remainder of files not shown ...') }}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div v-else>
                        <!-- Action Listing View -->
                        <div class="ida-heading">
                            {{ t('ida', capitalize(currentStatus) + ' Actions') }}
                        </div>
                        <div class="ida-table-wrapper">
                            <table class="ida-table" v-if="currentActions.length > 0">
                                <thead>
                                    <tr>
                                        <th class="ida-wide-cell">
                                            {{ t('ida', 'Action ID') }}
                                        </th>
                                        <th class="ida-wide-cell">
                                            {{ t('ida', capitalize(getTimestampFieldName(currentStatus))) }}
                                        </th>
                                        <th class="ida-narrow-cell">
                                            {{ t('ida', 'Action') }}
                                        </th>
                                        <th class="ida-narrow-cell">
                                            {{ t('ida', 'Project') }}
                                        </th>
                                        <th>
                                            {{ t('ida', 'Scope') }}
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="action in currentActions" :key="action.pid">
                                        <td class="fixed-width ida-link" @click="openActionDetails(action.pid)">
                                            {{ action.pid }}
                                        </td>
                                        <td class="fixed-width">
                                            {{ currentStatus === 'pending' ? action.initiated : action[currentStatus] }}
                                        </td>
                                        <td>{{ t('ida', capitalize(action.action)) }}</td>
                                        <td>{{ action.project }}</td>
                                        <td class="fixed-width">{{ action.pathname }}</td>
                                    </tr>
                                </tbody>
                            </table>
                            <div v-else>
                                {{ t('ida', 'No ' + currentStatus + ' actions found.') }}
                            </div>
                        </div>
                    </div>
                </div>
            </template>
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/dist/Components/NcContent.js'
import NcAppContent from '@nextcloud/vue/dist/Components/NcAppContent.js'
import NcAppNavigation from '@nextcloud/vue/dist/Components/NcAppNavigation.js'
import NcAppNavigationItem from '@nextcloud/vue/dist/Components/NcAppNavigationItem.js'
import IconDotsHorizontalCircleOutline from 'vue-material-design-icons/DotsHorizontalCircleOutline.vue'
import IconCheckCircleOutline from 'vue-material-design-icons/CheckCircleOutline.vue'
import IconAlertCircleOutline from 'vue-material-design-icons/AlertCircleOutline.vue'
import IconCloseCircleOutline from 'vue-material-design-icons/CloseCircleOutline.vue'
import { showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'
import { t } from '@nextcloud/l10n'
import { MAX_FILE_COUNT, STAGING_FOLDER_SUFFIX } from '../js/constants.js'

export default {

    name: 'App',

    props: {
        status: {
            type: String,
            required: false,
            default: 'pending',
        },
        pid: {
            type: String,
            required: false,
            default: null,
        },
    },

    components: {
        NcContent,
        NcAppNavigation,
        NcAppNavigationItem,
        NcAppContent,
        IconDotsHorizontalCircleOutline,
        IconCheckCircleOutline,
        IconAlertCircleOutline,
        IconCloseCircleOutline,
    },

    data() {
        return {
            currentActions: [],
            currentAction: {},
            currentActionFiles: [],
            currentStatus: this.status || null,
            maxFileCount: MAX_FILE_COUNT,
        };
    },

    watch: {
        status(newStatus) {
            console.debug('watch: status: ', newStatus);
            console.debug('watch: currentStatus:', this.currentStatus);
            if (newStatus) this.fetchActions(newStatus);
        },
        pid(newPid) {
            console.debug('watch: pid: ', newPid);
            console.debug('watch: currentActionPid:', this.currentAction.pid);
            if (newPid) this.fetchAction(newPid);
        },
    },

    mounted() {
        console.debug('mounted: params: ', this.$route.params);
        console.debug('mounted: fullPath:', this.$route.fullPath);
        console.debug('mounted: currentStatus:', this.currentStatus);
        console.debug('mounted: currentActionPid:', this.currentAction.pid);
        if (this.$route.params.pid) {
            this.fetchAction(this.$route.params.pid);
        } else if (this.pid) {
            this.fetchAction(this.pid);
        } else if (this.$route.params.status) {
            this.fetchActions(this.$route.params.status);
        } else {
            this.fetchActions(this.currentStatus);
        }
    },

    methods: {

        reportError(message) {
            showError(t('ida', message), { timeout: -1 })
        },

        openActionListing(newStatus = 'pending') {
            console.debug('openActionListing: newStatus: ', newStatus);
            try {
                if (newStatus !== this.currentStatus) {
                    console.debug('openActionListing: fullPath:', this.$route.fullPath);
                    const newPath = `/apps/ida/actions/${newStatus}`;
                    console.debug(`openActionListing: newPath: ${newPath}`);
                    if (this.$route.fullPath !== newPath) {
                        console.debug(`openActionListing: push: ${newPath}`);
                        this.$router.push({ name: 'ActionListing', params: { status: newStatus } });
                        // Bug in Chrome requires this brute force reload
                        window.location.reload();
                    }
                }
            } catch (error) {
                this.reportError(t('ida', 'Failed to open action listing') + ': ' + error);
            }
        },

        openActionDetails(newPid) {
            console.debug('openActionDetails: newPid: ', newPid);
            try {
                if (newPid && newPid !== this.currentAction.pid) {
                    console.debug('openActionDetails: fullPath:', this.$route.fullPath);
                    const newPath = `/apps/ida/action/${newPid}`;
                    console.debug(`openActionDetails: newPath: ${newPath}`);
                    if (this.$route.fullPath !== newPath) {
                        console.debug(`openActionDetails: push: ${newPath}`);
                        this.$router.push({ name: 'ActionDetails', params: { pid: newPid } });
                        // Bug in Chrome requires this brute force reload
                        window.location.reload();
                    }
                }
            } catch (error) {
                this.reportError(t('ida', 'Failed to load action details') + ': ' + error);
            }
        },

        async fetchActions(newStatus = 'pending') {
            console.debug('fetchActions: newStatus: ', newStatus);
            try {
                const response = await fetch(`/apps/ida/api/actions?status=${newStatus}`);
                if (!response.ok) {
                    this.reportError(t('ida', 'Failed to retrieve actions') + ': ' + response.statusText);
                    return;
                }
                const data = await response.json();
                this.currentActions = data || [];
                this.currentAction = {};
                this.currentActionFiles = [];
                this.currentStatus = newStatus;
            } catch (error) {
                this.reportError(t('ida', 'Failed to load action listing') + ': ' + error);
            }
        },

        async fetchAction(newPid) {
            console.debug('fetchAction: newPid: ', newPid);
            try {
                if (newPid && newPid !== this.currentAction.pid) {
                    const response = await fetch(`/apps/ida/api/actions/${newPid}`);
                    if (!response.ok) {
                        this.reportError(t('ida', 'Failed to retrieve action details') + ': ' + response.statusText);
                        return;
                    }
                    const data = await response.json();
                    this.currentStatus = null;
                    this.currentAction = data || {};
                    this.currentActionFiles = [];
                    if (this.currentAction.action) {
                        this.fetchActionFiles(this.currentAction.action, this.currentAction.pid);
                    }
                }
            } catch (error) {
                this.reportError(t('ida', 'Failed to load action details') + ': ' + error);
            }
        },

        async fetchActionFiles(action, pid) {
            console.debug('fetchActionFiles: action: ', action, ' pid: ', pid);
            try {
                const response = await fetch(`/apps/ida/api/files/action/${pid}`);
                if (!response.ok) {
                    this.reportError(t('ida', 'Failed to retrieve action files') + ': ' + response.statusText);
                    return;
                }
                const data = await response.json();
                data.forEach(file => {
                    if (file.project && file.pathname) {
                        const dirname  = file.pathname.substring(0, file.pathname.lastIndexOf('/'));
                        const filename = file.pathname.substring(file.pathname.lastIndexOf('/') + 1);
                        const suffix = (action === 'freeze') ? '' : STAGING_FOLDER_SUFFIX;
                        const dirParameter = encodeURIComponent(`/${file.project}${suffix}${dirname}`);
                        const fileParameter = encodeURIComponent(filename);
                        file.url = `/apps/files/?dir=${dirParameter}&ida-action-filename=${fileParameter}`;
                    }
                });
                this.currentActionFiles = data || [];
            } catch (error) {
                this.reportError(t('ida', 'Failed to load action files') + ': ' + error);
            }
        },

        async retryAction(pid) {
            console.debug('retryAction: pid: ', pid);
            try {
                const response = await fetch(`/apps/ida/api/retry/${pid}`, { method: 'POST' });
                if (!response.ok) {
                    this.reportError(t('ida', 'Failed to retry action') + ': ' + response.statusText);
                    return;
                }
                this.openActionDetails(pid);
            } catch (error) {
                this.reportError(t('ida', 'Failed to retry action') + ': ' + error);
            }
        },

        capitalize(s) {
            return s.charAt(0).toUpperCase() + s.slice(1)
        },

        getTimestampFieldName(status) {
            return status === 'pending' ? 'initiated' : status;
        },

        getTimestamp(status, action) {
            switch (status) {
                case 'completed':
                    return action.completed;
                case 'failed':
                    return action.failed;
                case 'cleared':
                    return action.cleared;
                default:
                    return action.initiated;
            }
        },
    },
};
</script>

<style scoped lang="scss">
.main-content {
    display: flex;
    height: 100%;
    flex-direction: column;
    padding-left: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    overflow: hidden;
    background-color: white;
}

.ida-heading {
    position: sticky;
    top: 0;
    z-index: 1;
    padding-top: 10px;
    padding-left: 30px;
    padding-bottom: 20px;
    font-size: larger;
    font-weight: bold;
}

.ida-link {
    color: #007FAD;
    text-decoration: none;
    cursor: pointer;
}

.gray-text {
    color: lightgray;
}

.ida-table-wrapper {
    flex-grow: 1;
    overflow-y: auto;
    height: 80vh;
}

.ida-table {
    width: 100%;
    border-collapse: collapse;
    overflow-y: scroll;
}

.ida-table th,
.ida-table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

.ida-table th {
    background-color: #f2f2f2;
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 9999;
}

table .ida-narrow-cell {
    width: 100px;
}

table th.ida-wide-cell {
    width: 200px;
}

table td.ida-wide-cell {
    max-width: 250px;
    white-space: nowrap;
    text-overflow: ellipsis;
}
</style>
