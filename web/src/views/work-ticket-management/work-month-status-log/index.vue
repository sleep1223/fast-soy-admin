<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteWorkMonthStatusLog, fetchDeleteWorkMonthStatusLog, fetchGetWorkMonthStatusLogList,
  fetchExportWorkMonthStatusLog, fetchImportWorkMonthStatusLog, fetchPreviewImportWorkMonthStatusLog, fetchWorkMonthStatusLogImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import WorkMonthStatusLogOperateDrawer from './modules/work-month-status-log-operate-drawer.vue';
import WorkMonthStatusLogSearch from './modules/work-month-status-log-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const fromStatusOptions = ref<SelectOptionItem[]>([]);
const toStatusOptions = ref<SelectOptionItem[]>([]);
const actionOptions = ref<SelectOptionItem[]>([]);
const workMonthOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.WorkMonthStatusLogSearchParams = {
  current: 1,
  size: 10,
  fromStatus: null,
  toStatus: null,
  action: null,
  reason: null,
  workMonthId: null,
};

const searchParams: Api.WorkTicketManagementManage.WorkMonthStatusLogSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetWorkMonthStatusLogList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'fromStatus', title: $t('page.work_ticket_management.work_month_status_log.fromStatus'), align: 'center', minWidth: 120 },
    { key: 'toStatus', title: $t('page.work_ticket_management.work_month_status_log.toStatus'), align: 'center', minWidth: 120 },
    { key: 'action', title: $t('page.work_ticket_management.work_month_status_log.action'), align: 'center', minWidth: 120 },
    { key: 'reason', title: $t('page.work_ticket_management.work_month_status_log.reason'), align: 'center', minWidth: 120 },
    { key: 'summary', title: $t('page.work_ticket_management.work_month_status_log.summary'), align: 'center', minWidth: 120 },
    { key: 'workMonthId', title: $t('page.work_ticket_management.work_month_status_log.workMonth'), align: 'center', minWidth: 120 },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => (
        <div class="flex-center gap-8px">
          <NButton type="primary" ghost size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
          <NPopconfirm onPositiveClick={() => handleDelete(row.id)}>
              {{
                default: () => $t('common.confirmDelete'),
                trigger: () => (
                  <NButton type="error" ghost size="small">
                    {$t('common.delete')}
                  </NButton>
                )
              }}
            </NPopconfirm>
        </div>
      )
    }
  ]
});

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onBatchDeleted, onDeleted } =
  useTableOperate(data, 'id', getData);

async function handleBatchDelete() {
  const { error } = await fetchBatchDeleteWorkMonthStatusLog({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteWorkMonthStatusLog({ id });
  if (!error) onDeleted();
}

function resetSearchParams() {
  Object.assign(searchParams, {
    ...defaultSearchParams
  });
  getDataByPage(1);
}

function edit(id: string) {
  handleEdit(id);
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <WorkMonthStatusLogSearch
      v-model:model="searchParams"
      :from-status-options="fromStatusOptions"
      :to-status-options="toStatusOptions"
      :action-options="actionOptions"
      :work-month-options="workMonthOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.work_month_status_log.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportWorkMonthStatusLog"
            :preview-api="fetchPreviewImportWorkMonthStatusLog"
            :export-api="() => fetchExportWorkMonthStatusLog(searchParams)"
            :export-selected-api="ids => fetchExportWorkMonthStatusLog({ ...searchParams, ids })"
            :selected-ids="checkedRowKeys"
            :template-api="fetchWorkMonthStatusLogImportTemplate"
            @imported="getDataByPage(1)"
          />
          <TableHeaderOperation
            v-model:columns="columnChecks"
            :disabled-delete="checkedRowKeys.length === 0"
            :loading="loading"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @refresh="getData"
          />
        </NSpace>
      </template>
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="600"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <WorkMonthStatusLogOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :from-status-options="fromStatusOptions"
        :to-status-options="toStatusOptions"
        :action-options="actionOptions"
        :work-month-options="workMonthOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
