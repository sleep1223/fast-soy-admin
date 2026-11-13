<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteMonthlyImportRow, fetchDeleteMonthlyImportRow, fetchGetMonthlyImportRowList,
  fetchExportMonthlyImportRow, fetchImportMonthlyImportRow, fetchPreviewImportMonthlyImportRow, fetchMonthlyImportRowImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import MonthlyImportRowOperateDrawer from './modules/monthly-import-row-operate-drawer.vue';
import MonthlyImportRowSearch from './modules/monthly-import-row-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const matchStatusOptions = ref<SelectOptionItem[]>([]);
const matchSourceOptions = ref<SelectOptionItem[]>([]);
const handlingStatusOptions = ref<SelectOptionItem[]>([]);
const batchOptions = ref<SelectOptionItem[]>([]);
const orderOptions = ref<SelectOptionItem[]>([]);
const duplicateOfRowOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.MonthlyImportRowSearchParams = {
  current: 1,
  size: 10,
  rowNumber: null,
  rawPartNo: null,
  normalizedPartNo: null,
  matchStatus: null,
  matchSource: null,
  sourceQuantity: null,
  handlingStatus: null,
  handlingNote: null,
  handledAtStart: null,
  handledAtEnd: null,
  handledBy: null,
  note: null,
  batchId: null,
  orderId: null,
  duplicateOfRowId: null,
};

const searchParams: Api.WorkTicketManagementManage.MonthlyImportRowSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetMonthlyImportRowList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'rowNumber', title: $t('page.work_ticket_management.monthly_import_row.rowNumber'), align: 'center', minWidth: 120 },
    { key: 'rawPartNo', title: $t('page.work_ticket_management.monthly_import_row.rawPartNo'), align: 'center', minWidth: 120 },
    { key: 'normalizedPartNo', title: $t('page.work_ticket_management.monthly_import_row.normalizedPartNo'), align: 'center', minWidth: 120 },
    { key: 'matchStatus', title: $t('page.work_ticket_management.monthly_import_row.matchStatus'), align: 'center', minWidth: 120 },
    { key: 'matchSource', title: $t('page.work_ticket_management.monthly_import_row.matchSource'), align: 'center', minWidth: 120 },
    { key: 'sourceQuantity', title: $t('page.work_ticket_management.monthly_import_row.sourceQuantity'), align: 'center', minWidth: 120 },
    { key: 'batchId', title: $t('page.work_ticket_management.monthly_import_row.batch'), align: 'center', minWidth: 120 },
    { key: 'orderId', title: $t('page.work_ticket_management.monthly_import_row.order'), align: 'center', minWidth: 120 },
    { key: 'duplicateOfRowId', title: $t('page.work_ticket_management.monthly_import_row.duplicateOfRow'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteMonthlyImportRow({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteMonthlyImportRow({ id });
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
    <MonthlyImportRowSearch
      v-model:model="searchParams"
      :match-status-options="matchStatusOptions"
      :match-source-options="matchSourceOptions"
      :handling-status-options="handlingStatusOptions"
      :batch-options="batchOptions"
      :order-options="orderOptions"
      :duplicate-of-row-options="duplicateOfRowOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.monthly_import_row.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportMonthlyImportRow"
            :preview-api="fetchPreviewImportMonthlyImportRow"
            :export-api="parentFields => fetchExportMonthlyImportRow({ ...searchParams, parentFields })"
            :export-selected-api="
              (ids, parentFields) => fetchExportMonthlyImportRow({ ...searchParams, ids, parentFields })
            "
            :export-parent-fields="[
              { name: 'row_number', label: $t('page.work_ticket_management.monthly_import_row.rowNumber') },
              { name: 'raw_part_no', label: $t('page.work_ticket_management.monthly_import_row.rawPartNo') },
              {
                name: 'normalized_part_no',
                label: $t('page.work_ticket_management.monthly_import_row.normalizedPartNo')
              },
              { name: 'match_status', label: $t('page.work_ticket_management.monthly_import_row.matchStatus') },
              { name: 'match_source', label: $t('page.work_ticket_management.monthly_import_row.matchSource') },
              { name: 'source_quantity', label: $t('page.work_ticket_management.monthly_import_row.sourceQuantity') },
              { name: 'raw_data', label: $t('page.work_ticket_management.monthly_import_row.rawData') },
              { name: 'handling_status', label: $t('page.work_ticket_management.monthly_import_row.handlingStatus') },
              { name: 'handling_note', label: $t('page.work_ticket_management.monthly_import_row.handlingNote') },
              { name: 'handled_at', label: $t('page.work_ticket_management.monthly_import_row.handledAt') },
              { name: 'handled_by', label: $t('page.work_ticket_management.monthly_import_row.handledBy') },
              { name: 'note', label: $t('page.work_ticket_management.monthly_import_row.note') },
              { name: 'batch_id', label: $t('page.work_ticket_management.monthly_import_row.batch') },
              { name: 'order_id', label: $t('page.work_ticket_management.monthly_import_row.order') },
              {
                name: 'duplicate_of_row_id',
                label: $t('page.work_ticket_management.monthly_import_row.duplicateOfRow')
              }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchMonthlyImportRowImportTemplate"
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
      <MonthlyImportRowOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :match-status-options="matchStatusOptions"
        :match-source-options="matchSourceOptions"
        :handling-status-options="handlingStatusOptions"
        :batch-options="batchOptions"
        :order-options="orderOptions"
        :duplicate-of-row-options="duplicateOfRowOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
