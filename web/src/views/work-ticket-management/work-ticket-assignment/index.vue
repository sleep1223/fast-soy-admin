<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteWorkTicketAssignment, fetchDeleteWorkTicketAssignment, fetchGetWorkTicketAssignmentList,
  fetchExportWorkTicketAssignment, fetchImportWorkTicketAssignment, fetchPreviewImportWorkTicketAssignment, fetchWorkTicketAssignmentImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import WorkTicketAssignmentOperateDrawer from './modules/work-ticket-assignment-operate-drawer.vue';
import WorkTicketAssignmentSearch from './modules/work-ticket-assignment-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const sourceOptions = ref<SelectOptionItem[]>([]);
const ticketOptions = ref<SelectOptionItem[]>([]);
const workerOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.WorkTicketAssignmentSearchParams = {
  current: 1,
  size: 10,
  source: null,
  remark: null,
  ticketId: null,
  workerId: null,
};

const searchParams: Api.WorkTicketManagementManage.WorkTicketAssignmentSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetWorkTicketAssignmentList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'source', title: $t('page.work_ticket_management.work_ticket_assignment.source'), align: 'center', minWidth: 120 },
    { key: 'remark', title: $t('page.work_ticket_management.work_ticket_assignment.remark'), align: 'center', minWidth: 120 },
    { key: 'ticketId', title: $t('page.work_ticket_management.work_ticket_assignment.ticket'), align: 'center', minWidth: 120 },
    { key: 'workerId', title: $t('page.work_ticket_management.work_ticket_assignment.worker'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteWorkTicketAssignment({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteWorkTicketAssignment({ id });
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
    <WorkTicketAssignmentSearch
      v-model:model="searchParams"
      :source-options="sourceOptions"
      :ticket-options="ticketOptions"
      :worker-options="workerOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.work_ticket_assignment.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportWorkTicketAssignment"
            :preview-api="fetchPreviewImportWorkTicketAssignment"
            :export-api="parentFields => fetchExportWorkTicketAssignment({ ...searchParams, parentFields })"
            :export-selected-api="
              (ids, parentFields) => fetchExportWorkTicketAssignment({ ...searchParams, ids, parentFields })
            "
            :export-parent-fields="[
              { name: 'source', label: $t('page.work_ticket_management.work_ticket_assignment.source') },
              { name: 'remark', label: $t('page.work_ticket_management.work_ticket_assignment.remark') },
              { name: 'ticket_id', label: $t('page.work_ticket_management.work_ticket_assignment.ticket') },
              { name: 'worker_id', label: $t('page.work_ticket_management.work_ticket_assignment.worker') }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchWorkTicketAssignmentImportTemplate"
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
      <WorkTicketAssignmentOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :source-options="sourceOptions"
        :ticket-options="ticketOptions"
        :worker-options="workerOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
