<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm, NSpace, NSwitch } from 'naive-ui';
import {
  fetchAddOrderUnitMapping,
  fetchAddProductionUnit,
  fetchAddWorker,
  fetchDeleteOrderUnitMapping,
  fetchDeleteProductionUnit,
  fetchDeleteWorker,
  fetchExportProductionUnit,
  fetchExportWorker,
  fetchGetOrderList,
  fetchGetProductionUnitList,
  fetchGetWorkerList,
  fetchImportProductionUnit,
  fetchImportWorker,
  fetchPreviewImportProductionUnit,
  fetchPreviewImportWorker,
  fetchSearchOrderUnitMappings,
  fetchProductionUnitImportTemplate,
  fetchUpdateProductionUnit,
  fetchUpdateWorker,
  fetchWorkerImportTemplate
} from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';

defineOptions({ name: 'WorkTicketMasterData' });

const { hasAuth } = useAuth();
const tab = ref<'units' | 'workers' | 'mappings'>('units');

const units = ref<Api.WorkTicketManagementManage.ProductionUnit[]>([]);
const unitLoading = ref(false);
const unitKeyword = ref('');
const unitPagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onUpdatePage: (page: number) => {
    unitPagination.page = page;
    loadUnits();
  },
  onUpdatePageSize: (size: number) => {
    unitPagination.pageSize = size;
    unitPagination.page = 1;
    loadUnits();
  }
});

function unitRowKey(row: Api.WorkTicketManagementManage.ProductionUnit) {
  return row.id;
}
function workerRowKey(row: Api.WorkTicketManagementManage.Worker) {
  return row.id;
}
function mappingRowKey(row: Api.WorkTicketManagement.MappingRow) {
  return row.id;
}
async function loadUnits() {
  unitLoading.value = true;
  const { data, error } = await fetchGetProductionUnitList({
    current: unitPagination.page,
    size: unitPagination.pageSize,
    code: unitKeyword.value || null,
    name: unitKeyword.value || null
  });
  unitLoading.value = false;
  if (!error && data) {
    units.value = data.records;
    unitPagination.itemCount = data.total;
  }
}

const workers = ref<Api.WorkTicketManagementManage.Worker[]>([]);
const workerLoading = ref(false);
const workerKeyword = ref('');
const workerPagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onUpdatePage: (page: number) => {
    workerPagination.page = page;
    loadWorkers();
  },
  onUpdatePageSize: (size: number) => {
    workerPagination.pageSize = size;
    workerPagination.page = 1;
    loadWorkers();
  }
});

async function loadWorkers() {
  workerLoading.value = true;
  const { data, error } = await fetchGetWorkerList({
    current: workerPagination.page,
    size: workerPagination.pageSize,
    name: workerKeyword.value || null,
    workerNo: workerKeyword.value || null
  });
  workerLoading.value = false;
  if (!error && data) {
    workers.value = data.records;
    workerPagination.itemCount = data.total;
  }
}

const mappings = ref<Api.WorkTicketManagement.MappingRow[]>([]);
const mappingLoading = ref(false);
const mappingKeyword = ref('');
const mappingPagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onUpdatePage: (page: number) => {
    mappingPagination.page = page;
    loadMappings();
  },
  onUpdatePageSize: (size: number) => {
    mappingPagination.pageSize = size;
    mappingPagination.page = 1;
    loadMappings();
  }
});

async function loadMappings() {
  mappingLoading.value = true;
  const { data, error } = await fetchSearchOrderUnitMappings({
    current: mappingPagination.page,
    size: mappingPagination.pageSize,
    keyword: mappingKeyword.value || null
  });
  mappingLoading.value = false;
  if (!error && data) {
    mappings.value = data.records;
    mappingPagination.itemCount = data.total;
  }
}

const unitFormVisible = ref(false);
const unitForm = reactive<{ id?: string; code: string; name: string; enabled: boolean; remark: string }>({
  id: undefined,
  code: '',
  name: '',
  enabled: true,
  remark: ''
});
function addUnit() {
  Object.assign(unitForm, { id: undefined, code: '', name: '', enabled: true, remark: '' });
  unitFormVisible.value = true;
}
function editUnit(row: Api.WorkTicketManagementManage.ProductionUnit) {
  Object.assign(unitForm, { ...row, id: row.id, enabled: row.enabled ?? true, remark: row.remark ?? '' });
  unitFormVisible.value = true;
}
async function saveUnit() {
  const { error } = unitForm.id
    ? await fetchUpdateProductionUnit({ ...unitForm, id: unitForm.id })
    : await fetchAddProductionUnit(unitForm);
  if (error) return;
  unitFormVisible.value = false;
  loadUnits();
}
async function removeUnit(id: string) {
  const { error } = await fetchDeleteProductionUnit({ id });
  if (!error) loadUnits();
}

const workerFormVisible = ref(false);
const workerForm = reactive<{ id?: string; workerNo: string; name: string; productionUnitId: string | null; enabled: boolean; remark: string }>({
  id: undefined,
  workerNo: '',
  name: '',
  productionUnitId: null,
  enabled: true,
  remark: ''
});
function addWorker() {
  Object.assign(workerForm, { id: undefined, workerNo: '', name: '', productionUnitId: null, enabled: true, remark: '' });
  workerFormVisible.value = true;
}
function editWorker(row: Api.WorkTicketManagementManage.Worker) {
  Object.assign(workerForm, { ...row, id: row.id, workerNo: row.workerNo ?? '', enabled: row.enabled ?? true, remark: row.remark ?? '' });
  workerFormVisible.value = true;
}
async function saveWorker() {
  const { error } = workerForm.id
    ? await fetchUpdateWorker({ ...workerForm, id: workerForm.id })
    : await fetchAddWorker(workerForm);
  if (error) return;
  workerFormVisible.value = false;
  loadWorkers();
}
async function removeWorker(id: string) {
  const { error } = await fetchDeleteWorker({ id });
  if (!error) loadWorkers();
}

const mappingVisible = ref(false);
const mappingForm = reactive<{ orderId: string | null; productionUnitId: string | null; remark: string }>({
  orderId: null,
  productionUnitId: null,
  remark: ''
});
const orderKeyword = ref('');
const orderOptions = ref<Api.OrderManagementManage.Order[]>([]);
const orderSearching = ref(false);
async function searchOrders(value: string) {
  orderKeyword.value = value.trim();
  if (!value.trim()) {
    orderOptions.value = [];
    return;
  }
  orderSearching.value = true;
  const { data, error } = await fetchGetOrderList({ current: 1, size: 20, partNo: value.trim(), orderNo: value.trim() });
  orderSearching.value = false;
  if (!error && data) orderOptions.value = data.records;
}
function addMapping() {
  Object.assign(mappingForm, { orderId: null, productionUnitId: null, remark: '' });
  orderKeyword.value = '';
  orderOptions.value = [];
  mappingVisible.value = true;
}
async function saveMapping() {
  if (!mappingForm.orderId || !mappingForm.productionUnitId) return;
  const { error } = await fetchAddOrderUnitMapping({
    orderId: mappingForm.orderId,
    productionUnitId: mappingForm.productionUnitId,
    remark: mappingForm.remark
  });
  if (error) return;
  mappingVisible.value = false;
  loadMappings();
}
async function removeMapping(id: string) {
  const { error } = await fetchDeleteOrderUnitMapping({ id });
  if (!error) loadMappings();
}

function unitName(id: string | null) {
  return units.value.find(unit => unit.id === id)?.name || id || '—';
}

const unitColumns = [
  { key: 'code', title: $t('page.work_ticket_management.production_unit.code'), width: 140 },
  { key: 'name', title: $t('page.work_ticket_management.production_unit.name'), minWidth: 160 },
  { key: 'enabled', title: $t('page.work_ticket_management.workflow.enabled'), width: 100, render: (row: Api.WorkTicketManagementManage.ProductionUnit) => (row.enabled ? $t('page.work_ticket_management.workflow.enabled') : $t('page.work_ticket_management.workflow.disabled')) },
  { key: 'remark', title: $t('page.work_ticket_management.workflow.remark'), minWidth: 180 },
  {
    key: 'actions',
    title: $t('page.work_ticket_management.workflow.actions'),
    width: 150,
    render: (row: Api.WorkTicketManagementManage.ProductionUnit) => (
      <NSpace size={8}>
        <NButton size="small" disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_EDIT')} onClick={() => editUnit(row)}>
          {$t('common.edit')}
        </NButton>
        <NPopconfirm onPositiveClick={() => removeUnit(row.id)}>
          {{
            default: () => $t('common.confirmDelete'),
            trigger: () => (
              <NButton size="small" type="error" ghost disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_DELETE')}>
                {$t('common.delete')}
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
];

const workerColumns = [
  { key: 'workerNo', title: $t('page.work_ticket_management.worker.workerNo'), width: 130 },
  { key: 'name', title: $t('page.work_ticket_management.worker.name'), minWidth: 140 },
  { key: 'productionUnitId', title: $t('page.work_ticket_management.worker.productionUnit'), minWidth: 160, render: (row: Api.WorkTicketManagementManage.Worker) => unitName(row.productionUnitId) },
  { key: 'enabled', title: $t('page.work_ticket_management.worker.enabled'), width: 100, render: (row: Api.WorkTicketManagementManage.Worker) => (row.enabled ? $t('page.work_ticket_management.workflow.enabled') : $t('page.work_ticket_management.workflow.disabled')) },
  {
    key: 'actions',
    title: $t('page.work_ticket_management.workflow.actions'),
    width: 150,
    render: (row: Api.WorkTicketManagementManage.Worker) => (
      <NSpace size={8}>
        <NButton size="small" disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_WORKER_EDIT')} onClick={() => editWorker(row)}>
          {$t('common.edit')}
        </NButton>
        <NPopconfirm onPositiveClick={() => removeWorker(row.id)}>
          {{
            default: () => $t('common.confirmDelete'),
            trigger: () => (
              <NButton size="small" type="error" ghost disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_WORKER_DELETE')}>
                {$t('common.delete')}
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
];

const mappingColumns = [
  { key: 'orderNo', title: $t('page.work_ticket_management.workflow.orderNo'), minWidth: 150 },
  { key: 'partNo', title: $t('page.work_ticket_management.workflow.partNo'), minWidth: 130 },
  { key: 'name', title: $t('page.work_ticket_management.workflow.name'), minWidth: 160 },
  { key: 'productionUnitName', title: $t('page.work_ticket_management.workflow.unit'), minWidth: 140 },
  { key: 'remark', title: $t('page.work_ticket_management.workflow.remark'), minWidth: 180 },
  {
    key: 'actions',
    title: $t('page.work_ticket_management.workflow.actions'),
    width: 100,
    render: (row: Api.WorkTicketManagement.MappingRow) => (
      <NPopconfirm onPositiveClick={() => removeMapping(row.id)}>
        {{
          default: () => $t('common.confirmDelete'),
          trigger: () => (
            <NButton size="small" type="error" ghost disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_DELETE')}>
              {$t('common.delete')}
            </NButton>
          )
        }}
      </NPopconfirm>
    )
  }
];

loadUnits();
loadWorkers();
loadMappings();
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="card-wrapper">
      <NTabs v-model:value="tab" type="line">
        <NTabPane name="units" :tab="$t('page.work_ticket_management.workflow.units')">
          <NSpace class="mb-12px" align="center" wrap>
            <NInput
              v-model:value="unitKeyword"
              clearable
              :placeholder="$t('page.work_ticket_management.workflow.search')"
              class="w-220px"
              @keyup.enter="loadUnits"
            />
            <NButton size="small" @click="loadUnits">{{ $t('page.work_ticket_management.workflow.search') }}</NButton>
            <NButton
              size="small"
              type="primary"
              :disabled="!hasAuth('B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_CREATE')"
              @click="addUnit"
            >
              {{ $t('page.work_ticket_management.workflow.addUnit') }}
            </NButton>
            <ExcelTransfer
              :import-api="fetchImportProductionUnit"
              :preview-api="fetchPreviewImportProductionUnit"
              :export-api="() => fetchExportProductionUnit({ current: 1, size: 1000 })"
              :template-api="fetchProductionUnitImportTemplate"
              @imported="loadUnits"
            />
          </NSpace>
          <NDataTable
            :columns="unitColumns"
            :data="units"
            :loading="unitLoading"
            remote
            :pagination="unitPagination"
            :row-key="unitRowKey"
            size="small"
          />
        </NTabPane>

        <NTabPane name="workers" :tab="$t('page.work_ticket_management.workflow.workers')">
          <NSpace class="mb-12px" align="center" wrap>
            <NInput
              v-model:value="workerKeyword"
              clearable
              :placeholder="$t('page.work_ticket_management.workflow.search')"
              class="w-220px"
              @keyup.enter="loadWorkers"
            />
            <NButton size="small" @click="loadWorkers">{{ $t('page.work_ticket_management.workflow.search') }}</NButton>
            <NButton
              size="small"
              type="primary"
              :disabled="!hasAuth('B_WORK_TICKET_MANAGEMENT_WORKER_CREATE')"
              @click="addWorker"
            >
              {{ $t('page.work_ticket_management.workflow.addWorker') }}
            </NButton>
            <ExcelTransfer
              :import-api="fetchImportWorker"
              :preview-api="fetchPreviewImportWorker"
              :export-api="() => fetchExportWorker({ current: 1, size: 1000 })"
              :template-api="fetchWorkerImportTemplate"
              @imported="loadWorkers"
            />
          </NSpace>
          <NDataTable
            :columns="workerColumns"
            :data="workers"
            :loading="workerLoading"
            remote
            :pagination="workerPagination"
            :row-key="workerRowKey"
            size="small"
          />
        </NTabPane>

        <NTabPane name="mappings" :tab="$t('page.work_ticket_management.workflow.mappings')">
          <NSpace class="mb-12px" align="center" wrap>
            <NInput
              v-model:value="mappingKeyword"
              clearable
              :placeholder="$t('page.work_ticket_management.workflow.search')"
              class="w-220px"
              @keyup.enter="loadMappings"
            />
            <NButton size="small" @click="loadMappings">
              {{ $t('page.work_ticket_management.workflow.search') }}
            </NButton>
            <NButton
              size="small"
              type="primary"
              :disabled="!hasAuth('B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_CREATE')"
              @click="addMapping"
            >
              {{ $t('page.work_ticket_management.workflow.addMapping') }}
            </NButton>
          </NSpace>
          <NDataTable
            :columns="mappingColumns"
            :data="mappings"
            :loading="mappingLoading"
            remote
            :pagination="mappingPagination"
            :row-key="mappingRowKey"
            size="small"
          />
        </NTabPane>
      </NTabs>
    </NCard>

    <NModal
      v-model:show="unitFormVisible"
      preset="card"
      :title="
        unitForm.id
          ? $t('page.work_ticket_management.production_unit.editProductionUnit')
          : $t('page.work_ticket_management.production_unit.addProductionUnit')
      "
      class="w-500px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.production_unit.code')" required>
          <NInput v-model:value="unitForm.code" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.production_unit.name')" required>
          <NInput v-model:value="unitForm.name" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.production_unit.enabled')">
          <NSwitch v-model:value="unitForm.enabled" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.production_unit.remark')">
          <NInput v-model:value="unitForm.remark" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="unitFormVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="saveUnit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="workerFormVisible"
      preset="card"
      :title="
        workerForm.id
          ? $t('page.work_ticket_management.worker.editWorker')
          : $t('page.work_ticket_management.worker.addWorker')
      "
      class="w-500px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.worker.workerNo')">
          <NInput v-model:value="workerForm.workerNo" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.name')" required>
          <NInput v-model:value="workerForm.name" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.productionUnit')">
          <NSelect
            v-model:value="workerForm.productionUnitId"
            :options="units.map(unit => ({ label: unit.name, value: unit.id }))"
            clearable
            filterable
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.enabled')">
          <NSwitch v-model:value="workerForm.enabled" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.remark')">
          <NInput v-model:value="workerForm.remark" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="workerFormVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="saveWorker">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="mappingVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.addMapping')"
      class="w-600px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.workflow.orderNo')" required>
          <NSelect
            v-model:value="mappingForm.orderId"
            remote
            filterable
            :loading="orderSearching"
            :options="
              orderOptions.map(order => ({
                label: `${order.partNo} | ${order.orderNo} | ${order.name}`,
                value: order.id
              }))
            "
            :placeholder="$t('page.work_ticket_management.workflow.orderCandidatesHint')"
            @search="searchOrders"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.unit')" required>
          <NSelect
            v-model:value="mappingForm.productionUnitId"
            :options="units.map(unit => ({ label: unit.name, value: unit.id }))"
            filterable
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.remark')">
          <NInput v-model:value="mappingForm.remark" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="mappingVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="saveMapping">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>
