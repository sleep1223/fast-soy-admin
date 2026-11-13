<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteMonthlyImportBatch, fetchDeleteMonthlyImportBatch, fetchGetMonthlyImportBatchList,
  fetchExportMonthlyImportBatch, fetchImportMonthlyImportBatch, fetchPreviewImportMonthlyImportBatch, fetchMonthlyImportBatchImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import MonthlyImportBatchOperateDrawer from './modules/monthly-import-batch-operate-drawer.vue';
import MonthlyImportBatchSearch from './modules/monthly-import-batch-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const sourceTypeOptions = ref<SelectOptionItem[]>([]);
const statusOptions = ref<SelectOptionItem[]>([]);
const workMonthOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.MonthlyImportBatchSearchParams = {
  current: 1,
  size: 10,
  sourceType: null,
  status: null,
  sourceName: null,
  contentHash: null,
  rowCount: null,
  voidReason: null,
  voidedAtStart: null,
  voidedAtEnd: null,
  voidedBy: null,
  remark: null,
  workMonthId: null,
};

const searchParams: Api.WorkTicketManagementManage.MonthlyImportBatchSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetMonthlyImportBatchList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'sourceType', title: $t('page.work_ticket_management.monthly_import_batch.sourceType'), align: 'center', minWidth: 120 },
    { key: 'status', title: $t('page.work_ticket_management.monthly_import_batch.status'), align: 'center', minWidth: 120 },
    { key: 'sourceName', title: $t('page.work_ticket_management.monthly_import_batch.sourceName'), align: 'center', minWidth: 120 },
    { key: 'contentHash', title: $t('page.work_ticket_management.monthly_import_batch.contentHash'), align: 'center', minWidth: 120 },
    { key: 'rowCount', title: $t('page.work_ticket_management.monthly_import_batch.rowCount'), align: 'center', minWidth: 120 },
    { key: 'voidReason', title: $t('page.work_ticket_management.monthly_import_batch.voidReason'), align: 'center', minWidth: 120 },
    { key: 'workMonthId', title: $t('page.work_ticket_management.monthly_import_batch.workMonth'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteMonthlyImportBatch({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteMonthlyImportBatch({ id });
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
    <MonthlyImportBatchSearch
      v-model:model="searchParams"
      :source-type-options="sourceTypeOptions"
      :status-options="statusOptions"
      :work-month-options="workMonthOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.monthly_import_batch.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportMonthlyImportBatch"
            :preview-api="fetchPreviewImportMonthlyImportBatch"
            :export-api="parentFields => fetchExportMonthlyImportBatch({ ...searchParams, parentFields })"
            :export-selected-api="
              (ids, parentFields) => fetchExportMonthlyImportBatch({ ...searchParams, ids, parentFields })
            "
            :export-parent-fields="[
              { name: 'source_type', label: $t('page.work_ticket_management.monthly_import_batch.sourceType') },
              { name: 'status', label: $t('page.work_ticket_management.monthly_import_batch.status') },
              { name: 'source_name', label: $t('page.work_ticket_management.monthly_import_batch.sourceName') },
              { name: 'content_hash', label: $t('page.work_ticket_management.monthly_import_batch.contentHash') },
              { name: 'row_count', label: $t('page.work_ticket_management.monthly_import_batch.rowCount') },
              { name: 'void_reason', label: $t('page.work_ticket_management.monthly_import_batch.voidReason') },
              { name: 'voided_at', label: $t('page.work_ticket_management.monthly_import_batch.voidedAt') },
              { name: 'voided_by', label: $t('page.work_ticket_management.monthly_import_batch.voidedBy') },
              { name: 'remark', label: $t('page.work_ticket_management.monthly_import_batch.remark') },
              { name: 'work_month_id', label: $t('page.work_ticket_management.monthly_import_batch.workMonth') }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchMonthlyImportBatchImportTemplate"
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
      <MonthlyImportBatchOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :source-type-options="sourceTypeOptions"
        :status-options="statusOptions"
        :work-month-options="workMonthOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
