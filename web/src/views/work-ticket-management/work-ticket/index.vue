<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteWorkTicket, fetchDeleteWorkTicket, fetchGetWorkTicketList,
  fetchExportWorkTicket, fetchImportWorkTicket, fetchPreviewImportWorkTicket, fetchWorkTicketImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import WorkTicketOperateDrawer from './modules/work-ticket-operate-drawer.vue';
import WorkTicketSearch from './modules/work-ticket-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const codeSourceOptions = ref<SelectOptionItem[]>([]);
const statusOptions = ref<SelectOptionItem[]>([]);
const reconcileStatusOptions = ref<SelectOptionItem[]>([]);
const workMonthOptions = ref<SelectOptionItem[]>([]);
const orderOptions = ref<SelectOptionItem[]>([]);
const sourceImportRowOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.WorkTicketSearchParams = {
  current: 1,
  size: 10,
  orderNoSnapshot: null,
  partNoSnapshot: null,
  nameSnapshot: null,
  ticketCode: null,
  ticketCodeKey: null,
  codeSource: null,
  codeRuleVersion: null,
  codeConfidence: null,
  status: null,
  reconcileStatus: null,
  reconcileNote: null,
  voidReason: null,
  voidedAtStart: null,
  voidedAtEnd: null,
  voidedBy: null,
  remark: null,
  revision: null,
  workMonthId: null,
  orderId: null,
  sourceImportRowId: null,
};

const searchParams: Api.WorkTicketManagementManage.WorkTicketSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetWorkTicketList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'orderNoSnapshot', title: $t('page.work_ticket_management.work_ticket.orderNoSnapshot'), align: 'center', minWidth: 120 },
    { key: 'partNoSnapshot', title: $t('page.work_ticket_management.work_ticket.partNoSnapshot'), align: 'center', minWidth: 120 },
    { key: 'nameSnapshot', title: $t('page.work_ticket_management.work_ticket.nameSnapshot'), align: 'center', minWidth: 120 },
    { key: 'ticketCode', title: $t('page.work_ticket_management.work_ticket.ticketCode'), align: 'center', minWidth: 120 },
    { key: 'ticketCodeKey', title: $t('page.work_ticket_management.work_ticket.ticketCodeKey'), align: 'center', minWidth: 120 },
    { key: 'codeSource', title: $t('page.work_ticket_management.work_ticket.codeSource'), align: 'center', minWidth: 120 },
    { key: 'workMonthId', title: $t('page.work_ticket_management.work_ticket.workMonth'), align: 'center', minWidth: 120 },
    { key: 'orderId', title: $t('page.work_ticket_management.work_ticket.order'), align: 'center', minWidth: 120 },
    { key: 'sourceImportRowId', title: $t('page.work_ticket_management.work_ticket.sourceImportRow'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteWorkTicket({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteWorkTicket({ id });
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
    <WorkTicketSearch
      v-model:model="searchParams"
      :code-source-options="codeSourceOptions"
      :status-options="statusOptions"
      :reconcile-status-options="reconcileStatusOptions"
      :work-month-options="workMonthOptions"
      :order-options="orderOptions"
      :source-import-row-options="sourceImportRowOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.work_ticket.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportWorkTicket"
            :preview-api="fetchPreviewImportWorkTicket"
            :export-api="parentFields => fetchExportWorkTicket({ ...searchParams, parentFields })"
            :export-selected-api="(ids, parentFields) => fetchExportWorkTicket({ ...searchParams, ids, parentFields })"
            :export-parent-fields="[
              { name: 'order_no_snapshot', label: $t('page.work_ticket_management.work_ticket.orderNoSnapshot') },
              { name: 'part_no_snapshot', label: $t('page.work_ticket_management.work_ticket.partNoSnapshot') },
              { name: 'name_snapshot', label: $t('page.work_ticket_management.work_ticket.nameSnapshot') },
              { name: 'ticket_code', label: $t('page.work_ticket_management.work_ticket.ticketCode') },
              { name: 'ticket_code_key', label: $t('page.work_ticket_management.work_ticket.ticketCodeKey') },
              { name: 'code_source', label: $t('page.work_ticket_management.work_ticket.codeSource') },
              { name: 'code_rule_version', label: $t('page.work_ticket_management.work_ticket.codeRuleVersion') },
              { name: 'code_confidence', label: $t('page.work_ticket_management.work_ticket.codeConfidence') },
              { name: 'status', label: $t('page.work_ticket_management.work_ticket.status') },
              { name: 'reconcile_status', label: $t('page.work_ticket_management.work_ticket.reconcileStatus') },
              { name: 'reconcile_note', label: $t('page.work_ticket_management.work_ticket.reconcileNote') },
              { name: 'void_reason', label: $t('page.work_ticket_management.work_ticket.voidReason') },
              { name: 'voided_at', label: $t('page.work_ticket_management.work_ticket.voidedAt') },
              { name: 'voided_by', label: $t('page.work_ticket_management.work_ticket.voidedBy') },
              { name: 'remark', label: $t('page.work_ticket_management.work_ticket.remark') },
              { name: 'revision', label: $t('page.work_ticket_management.work_ticket.revision') },
              { name: 'work_month_id', label: $t('page.work_ticket_management.work_ticket.workMonth') },
              { name: 'order_id', label: $t('page.work_ticket_management.work_ticket.order') },
              { name: 'source_import_row_id', label: $t('page.work_ticket_management.work_ticket.sourceImportRow') }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchWorkTicketImportTemplate"
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
      <WorkTicketOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :code-source-options="codeSourceOptions"
        :status-options="statusOptions"
        :reconcile-status-options="reconcileStatusOptions"
        :work-month-options="workMonthOptions"
        :order-options="orderOptions"
        :source-import-row-options="sourceImportRowOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
