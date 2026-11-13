<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteWorker, fetchDeleteWorker, fetchGetWorkerList,
  fetchExportWorker, fetchImportWorker, fetchPreviewImportWorker, fetchWorkerImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import WorkerOperateDrawer from './modules/worker-operate-drawer.vue';
import WorkerSearch from './modules/worker-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const productionUnitOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.WorkerSearchParams = {
  current: 1,
  size: 10,
  workerNo: null,
  name: null,
  enabled: null,
  remark: null,
  productionUnitId: null,
};

const searchParams: Api.WorkTicketManagementManage.WorkerSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetWorkerList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'workerNo', title: $t('page.work_ticket_management.worker.workerNo'), align: 'center', minWidth: 120 },
    { key: 'name', title: $t('page.work_ticket_management.worker.name'), align: 'center', minWidth: 120 },
    { key: 'enabled', title: $t('page.work_ticket_management.worker.enabled'), align: 'center', minWidth: 120 },
    { key: 'remark', title: $t('page.work_ticket_management.worker.remark'), align: 'center', minWidth: 120 },
    { key: 'productionUnitId', title: $t('page.work_ticket_management.worker.productionUnit'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteWorker({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteWorker({ id });
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
    <WorkerSearch
      v-model:model="searchParams"
      :production-unit-options="productionUnitOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.worker.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportWorker"
            :preview-api="fetchPreviewImportWorker"
            :export-api="parentFields => fetchExportWorker({ ...searchParams, parentFields })"
            :export-selected-api="(ids, parentFields) => fetchExportWorker({ ...searchParams, ids, parentFields })"
            :export-parent-fields="[
              { name: 'worker_no', label: $t('page.work_ticket_management.worker.workerNo') },
              { name: 'name', label: $t('page.work_ticket_management.worker.name') },
              { name: 'enabled', label: $t('page.work_ticket_management.worker.enabled') },
              { name: 'remark', label: $t('page.work_ticket_management.worker.remark') },
              { name: 'production_unit_id', label: $t('page.work_ticket_management.worker.productionUnit') }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchWorkerImportTemplate"
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
      <WorkerOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :production-unit-options="productionUnitOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
