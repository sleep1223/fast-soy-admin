<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteLaborProject, fetchDeleteLaborProject, fetchGetLaborProjectList,
  fetchExportLaborProject, fetchImportLaborProject, fetchPreviewImportLaborProject, fetchLaborProjectImportTemplate,
  fetchGetOrderList, fetchGetLaborWorkerList
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import LaborProjectOperateDrawer from './modules/labor-project-operate-drawer.vue';
import LaborProjectSearch from './modules/labor-project-search.vue';
import LaborWorkHourOperateDrawer from '../labor-work-hour/modules/labor-work-hour-operate-drawer.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();
const ordersVisible = ref(false);
const ordersLoading = ref(false);
const selectedProject = ref('');
const orders = ref<Api.OrderManagementManage.Order[]>([]);
const ticketVisible = ref(false);
const ticketOrderNo = ref('');
const workers = ref<{ label: string; value: string }[]>([]);
let orderRequest = 0;

async function showOrders(partNo: string) {
  const requestId = ++orderRequest;
  selectedProject.value = partNo;
  orders.value = [];
  ordersVisible.value = true;
  ordersLoading.value = true;
  try {
    const found: Api.OrderManagementManage.Order[] = [];
    let page = 1;
    let received = 0;
    let total = 0;
    do {
      const { data: result, error } = await fetchGetOrderList({ current: page, size: 1000, partNo });
      if (requestId !== orderRequest || error || !result) return;
      found.push(...result.records.filter(order => order.partNo === partNo));
      received += result.records.length;
      total = result.total;
      if (!result.records.length) break;
      page += 1;
    } while (received < total);
    orders.value = found;
  } finally {
    if (requestId === orderRequest) ordersLoading.value = false;
  }
}

async function addTicket(orderNo: string) {
  const options: { label: string; value: string }[] = [];
  let page = 1;
  let total = 0;
  do {
    const { data: result, error } = await fetchGetLaborWorkerList({ current: page, size: 1000 });
    if (error || !result) return;
    options.push(...result.records.map(worker => ({ label: `${worker.name}（${worker.employeeNo}）`, value: worker.id })));
    total = result.total;
    if (!result.records.length) break;
    page += 1;
  } while (options.length < total);
  workers.value = options;
  ticketOrderNo.value = orderNo;
  ticketVisible.value = true;
}

const orderColumns = [
  { key: 'orderNo', title: $t('page.labor_management.labor_work_hour.orderNo') },
  { key: 'name', title: $t('page.labor_management.labor_project.orderName') },
  { key: 'operate', title: $t('common.operate'), render: (row: Api.OrderManagementManage.Order) => (
    <NButton disabled={!hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')} size="small" onClick={() => addTicket(row.orderNo)}>
      {$t('page.labor_management.labor_project.addTicket')}
    </NButton>
  ) }
];



const defaultSearchParams: Api.LaborManagementManage.LaborProjectSearchParams = {
  current: 1,
  size: 10,
  partNo: null,
};

const searchParams: Api.LaborManagementManage.LaborProjectSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetLaborProjectList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'partNo', title: $t('page.labor_management.labor_project.partNo'), align: 'center', minWidth: 120 },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => (
        <div class="flex-center gap-8px">
          <NButton size="small" onClick={() => showOrders(row.partNo)}>{$t('page.labor_management.labor_project.viewOrders')}</NButton>
          {hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_EDIT') && (
              <NButton type="primary" ghost size="small" onClick={() => edit(row.id)}>
                {$t('common.edit')}
              </NButton>
            )}
          {hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_DELETE') && (
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
            )}
        </div>
      )
    }
  ]
});

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onBatchDeleted, onDeleted } =
  useTableOperate(data, 'id', getData);

async function handleBatchDelete() {
  const { error } = await fetchBatchDeleteLaborProject({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteLaborProject({ id });
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
    <LaborProjectSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard
      :title="$t('page.labor_management.labor_project.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportLaborProject"
            :preview-api="fetchPreviewImportLaborProject"
            :export-api="() => fetchExportLaborProject(searchParams)"
            :export-selected-api="ids => fetchExportLaborProject({ ...searchParams, ids })"
            :selected-ids="checkedRowKeys"
            :template-api="fetchLaborProjectImportTemplate"
            :can-import="hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_IMPORT')"
            :can-export="hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_EXPORT')"
            @imported="getDataByPage(1)"
          />
          <TableHeaderOperation v-model:columns="columnChecks" :loading="loading" @refresh="getData">
            <NButton
              v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_CREATE')"
              size="small"
              ghost
              type="primary"
              @click="handleAdd"
            >
              <template #icon><icon-ic-round-plus class="text-icon" /></template>
              {{ $t('common.add') }}
            </NButton>
            <NPopconfirm v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_DELETE')" @positive-click="handleBatchDelete">
              <template #trigger>
                <NButton size="small" ghost type="error" :disabled="checkedRowKeys.length === 0">
                  <template #icon><icon-ic-round-delete class="text-icon" /></template>
                  {{ $t('common.batchDelete') }}
                </NButton>
              </template>
              {{ $t('common.confirmDelete') }}
            </NPopconfirm>
          </TableHeaderOperation>
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
      <LaborProjectOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
      <NModal
        v-model:show="ordersVisible"
        preset="card"
        :title="`${$t('page.labor_management.labor_project.viewOrders')}：${selectedProject}`"
        class="max-w-900px"
      >
        <NDataTable
          :columns="orderColumns"
          :data="orders"
          :loading="ordersLoading"
          :pagination="{ pageSize: 10 }"
          :row-key="row => row.id"
        />
      </NModal>
      <LaborWorkHourOperateDrawer
        v-model:visible="ticketVisible"
        operate-type="add"
        :initial-order-no="ticketOrderNo"
        :worker-options="workers"
      />
    </NCard>
  </div>
</template>
