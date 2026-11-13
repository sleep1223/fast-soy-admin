<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteWorkTimeEntry, fetchDeleteWorkTimeEntry, fetchGetWorkTimeEntryList,
  fetchExportWorkTimeEntry, fetchImportWorkTimeEntry, fetchPreviewImportWorkTimeEntry, fetchWorkTimeEntryImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import WorkTimeEntryOperateDrawer from './modules/work-time-entry-operate-drawer.vue';
import WorkTimeEntrySearch from './modules/work-time-entry-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const assignmentOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.WorkTimeEntrySearchParams = {
  current: 1,
  size: 10,
  workDateStart: null,
  workDateEnd: null,
  accountingMonth: null,
  hours: null,
  remark: null,
  assignmentId: null,
};

const searchParams: Api.WorkTicketManagementManage.WorkTimeEntrySearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetWorkTimeEntryList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'workDate', title: $t('page.work_ticket_management.work_time_entry.workDate'), align: 'center', minWidth: 120 },
    { key: 'accountingMonth', title: $t('page.work_ticket_management.work_time_entry.accountingMonth'), align: 'center', minWidth: 120 },
    { key: 'hours', title: $t('page.work_ticket_management.work_time_entry.hours'), align: 'center', minWidth: 120 },
    { key: 'remark', title: $t('page.work_ticket_management.work_time_entry.remark'), align: 'center', minWidth: 120 },
    { key: 'assignmentId', title: $t('page.work_ticket_management.work_time_entry.assignment'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteWorkTimeEntry({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteWorkTimeEntry({ id });
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
    <WorkTimeEntrySearch
      v-model:model="searchParams"
      :assignment-options="assignmentOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.work_time_entry.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportWorkTimeEntry"
            :preview-api="fetchPreviewImportWorkTimeEntry"
            :export-api="() => fetchExportWorkTimeEntry(searchParams)"
            :export-selected-api="ids => fetchExportWorkTimeEntry({ ...searchParams, ids })"
            :selected-ids="checkedRowKeys"
            :template-api="fetchWorkTimeEntryImportTemplate"
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
      <WorkTimeEntryOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :assignment-options="assignmentOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
