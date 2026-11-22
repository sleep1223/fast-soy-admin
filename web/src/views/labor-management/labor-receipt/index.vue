<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NDescriptions, NDescriptionsItem, NEmpty, NSpace, NSpin } from 'naive-ui';
import {
  fetchGetLaborReceiptList,
  fetchGetLaborWorkerList,
  fetchGetLaborWorkHourList,
  fetchGetOrderList,
  fetchImportLaborReceipts
} from '@/service/api';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import LaborWorkHourOperateDrawer from '../labor-work-hour/modules/labor-work-hour-operate-drawer.vue';

const { hasAuth } = useAuth();
const month = ref<string | null>(null);
const file = ref<File | null>(null);
const importing = ref(false);
const openReceipt = ref<string | null>(null);
const loadingOrders = ref(false);
const loadFailed = ref(false);
const matchedOrders = ref<Api.OrderManagementManage.Order[]>([]);
const tickets = ref<Api.LaborManagementManage.LaborWorkHour[]>([]);
const receiptId = ref<string | null>(null);
const orderNo = ref('');
const ticketVisible = ref(false);
const workers = ref<{ label: string; value: string }[]>([]);
let requestSequence = 0;

const params = reactive<Api.LaborManagementManage.LaborReceiptSearchParams>({
  current: 1,
  size: 10,
  receiptMonthStart: null,
  receiptMonthEnd: null,
  partNo: null
});
const { data, loading, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetLaborReceiptList(params),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: value => {
    params.current = value.page;
    params.size = value.pageSize;
  },
  columns: () => []
});

function applyMonth() {
  params.receiptMonthStart = month.value;
  params.receiptMonthEnd = month.value;
  openReceipt.value = null;
  getDataByPage(1);
}

function selectFile(event: Event) {
  const input = event.target as HTMLInputElement;
  file.value = input.files?.[0] ?? null;
  input.value = '';
}

async function importFile() {
  if (!file.value || !month.value || importing.value) return;
  importing.value = true;
  try {
    const { data: result, error } = await fetchImportLaborReceipts(file.value, month.value);
    if (error || !result) return;
    window.$message?.success(
      `${$t('page.labor_management.labor_receipt.imported')}: ${result.createdCount}; ${$t('page.labor_management.labor_receipt.skipped')}: ${result.skippedCount}`
    );
    file.value = null;
    applyMonth();
  } finally {
    importing.value = false;
  }
}

async function expand(row: Api.LaborManagementManage.LaborReceipt) {
  if (openReceipt.value === row.id) {
    openReceipt.value = null;
    requestSequence += 1;
    return;
  }
  const requestId = ++requestSequence;
  openReceipt.value = row.id;
  matchedOrders.value = [];
  tickets.value = [];
  loadingOrders.value = true;
  loadFailed.value = false;
  try {
    const records: Api.OrderManagementManage.Order[] = [];
    let page = 1,
      received = 0,
      total = 0;
    do {
      const { data: result, error } = await fetchGetOrderList({ current: page, size: 1000, partNo: row.partNo });
      if (requestId !== requestSequence) return;
      if (error || !result) {
        loadFailed.value = true;
        return;
      }
      records.push(...result.records.filter(order => order.partNo === row.partNo));
      received += result.records.length;
      total = result.total;
      if (!result.records.length) break;
      page += 1;
    } while (received < total);
    matchedOrders.value = records;
    const entries: Api.LaborManagementManage.LaborWorkHour[] = [];
    page = 1;
    do {
      const { data: result, error } = await fetchGetLaborWorkHourList({ current: page, size: 1000, receiptId: row.id });
      if (requestId !== requestSequence) return;
      if (error || !result) {
        loadFailed.value = true;
        return;
      }
      entries.push(...result.records);
      total = result.total;
      if (!result.records.length) break;
      page += 1;
    } while (entries.length < total);
    tickets.value = entries;
    await loadWorkers();
  } finally {
    if (requestId === requestSequence) loadingOrders.value = false;
  }
}

function refreshTickets() {
  const row = data.value.find(item => item.id === receiptId.value);
  if (row) {
    openReceipt.value = null;
    expand(row);
  }
}

async function loadWorkers(): Promise<boolean> {
  const options: { label: string; value: string }[] = [];
  let page = 1,
    total = 0;
  do {
    const { data: result, error } = await fetchGetLaborWorkerList({ current: page, size: 1000 });
    if (error || !result) return false;
    options.push(
      ...result.records.map(worker => ({ label: `${worker.name}（${worker.employeeNo}）`, value: worker.id }))
    );
    total = result.total;
    if (!result.records.length) break;
    page += 1;
  } while (options.length < total);
  workers.value = options;
  return true;
}

async function addTicket(row: Api.LaborManagementManage.LaborReceipt, order: Api.OrderManagementManage.Order) {
  if (!(await loadWorkers())) return;
  receiptId.value = row.id;
  orderNo.value = order.orderNo;
  ticketVisible.value = true;
}

const orderFields = [
  'orderNo',
  'partNo',
  'name',
  'netWeight',
  'grossWeight',
  'unit',
  'quantity',
  'receivedQuantity',
  'totalWeight',
  'orderDueDate',
  'completedDate',
  'processRoute',
  'customer'
] as const;
</script>

<template>
  <NCard :title="$t('page.labor_management.labor_receipt.title')">
    <NSpace vertical>
      <NSpace align="center" wrap>
        <NDatePicker v-model:formatted-value="month" type="month" value-format="yyyy-MM-dd" clearable />
        <NButton @click="applyMonth">{{ $t('common.search') }}</NButton>
        <template v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_RECEIPT_IMPORT')">
          <input type="file" accept=".xlsx" @change="selectFile" />
          <span v-if="file">{{ file.name }}</span>
          <NPopconfirm @positive-click="importFile">
            <template #trigger>
              <NButton :disabled="!month || !file" :loading="importing">
                {{ $t('page.labor_management.labor_receipt.import') }}
              </NButton>
            </template>
            {{ $t('page.labor_management.labor_receipt.confirmImport') }}
          </NPopconfirm>
        </template>
      </NSpace>
      <NSpin :show="loading">
        <NEmpty v-if="!data.length" :description="$t('common.noData')" />
        <NCard v-for="row in data" :key="row.id" size="small" class="mb-12px">
          <template #header>
            <NButton text type="primary" @click="expand(row)">{{ row.partNo }}</NButton>
            · {{ row.receiptMonth.slice(0, 7) }}
          </template>
          <template v-if="openReceipt === row.id">
            <NSpin :show="loadingOrders">
              <NAlert v-if="!loadingOrders && loadFailed" type="error">
                {{ $t('page.labor_management.labor_receipt.loadFailed') }}
              </NAlert>
              <NEmpty
                v-else-if="!loadingOrders && !matchedOrders.length"
                :description="$t('page.labor_management.labor_receipt.unmatched')"
              />
              <NCard v-for="order in matchedOrders" :key="order.id" size="small" class="mb-12px">
                <template #header>{{ order.orderNo }}</template>
                <template #header-extra>
                  <NButton
                    v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')"
                    size="small"
                    @click="addTicket(row, order)"
                  >
                    {{ $t('page.labor_management.labor_project.addTicket') }}
                  </NButton>
                </template>
                <NDescriptions :column="2" bordered>
                  <NDescriptionsItem
                    v-for="field in orderFields"
                    :key="field"
                    :label="$t(`page.order_management.order.${field}`)"
                  >
                    {{ order[field] ?? '—' }}
                  </NDescriptionsItem>
                </NDescriptions>
                <NDescriptions
                  v-for="ticket in tickets.filter(item => item.orderNo === order.orderNo)"
                  :key="ticket.id"
                  :column="2"
                  bordered
                  class="mt-12px"
                >
                  <NDescriptionsItem :label="$t('page.labor_management.labor_work_hour.ticketCode')">
                    {{ ticket.ticketCode }}
                  </NDescriptionsItem>
                  <NDescriptionsItem :label="$t('page.labor_management.labor_work_hour.workHours')">
                    {{ ticket.workHours }}
                  </NDescriptionsItem>
                  <NDescriptionsItem :label="$t('page.labor_management.labor_work_hour.worker')">
                    {{ workers.find(worker => worker.value === ticket.workerId)?.label ?? ticket.workerId ?? '—' }}
                  </NDescriptionsItem>
                  <NDescriptionsItem :label="$t('page.labor_management.labor_work_hour.allocationMonth')">
                    {{ ticket.allocationMonth?.slice(0, 7) ?? '—' }}
                  </NDescriptionsItem>
                </NDescriptions>
              </NCard>
            </NSpin>
          </template>
        </NCard>
      </NSpin>
      <NPagination v-bind="mobilePagination" />
    </NSpace>
    <LaborWorkHourOperateDrawer
      v-model:visible="ticketVisible"
      operate-type="add"
      :initial-order-no="orderNo"
      :receipt-id="receiptId"
      :worker-options="workers"
      @submitted="refreshTickets"
    />
  </NCard>
</template>
