<script setup lang="tsx">
import { onMounted, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NPopconfirm, NSpace } from 'naive-ui';
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';
import {
  downloadExcel
} from '@/utils/excel';
import {
  fetchAssignTicket,
  fetchBatchAssignTickets,
  fetchCreateTicket,
  fetchExportTickets,
  fetchOcrCandidates,
  fetchOpenWorkMonth,
  fetchOrderCandidates,
  fetchPasteTicketCodes,
  fetchProductionUnitOptions,
  fetchReconcileTicket,
  fetchTicket,
  fetchTickets,
  fetchUnassignTicket,
  fetchUpdateTicket,
  fetchVoidTicket
} from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import StatusTag from '../shared/status-tag.vue';
import WorkerSelect from '../shared/worker-select.vue';

defineOptions({ name: 'WorkTicketLedger' });

const { hasAuth } = useAuth();
const month = ref(dayjs().format('YYYY-MM'));
const unitId = ref<string | null>(null);
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const tickets = ref<Api.WorkTicketManagement.Ticket[]>([]);
const loading = ref(false);
const checkedRowKeys = ref<string[]>([]);
const search = reactive({
  current: 1,
  size: 20,
  keyword: null as string | null,
  status: null as string | null,
  reconcileStatus: null as string | null,
  assignmentStatus: 'all' as 'all' | 'assigned' | 'unassigned',
  timeStatus: 'all' as 'all' | 'logged' | 'none'
});
const total = ref(0);

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
}
async function load() {
  loading.value = true;
  const { data, error } = await fetchTickets({
    workMonthId: null,
    productionUnitId: unitId.value,
    yearMonthStart: month.value,
    yearMonthEnd: month.value,
    status: (search.status as Api.WorkTicketManagement.TicketStatus | null) || null,
    reconcileStatus: (search.reconcileStatus as Api.WorkTicketManagement.ReconcileStatus | null) || null,
    assignmentStatus: search.assignmentStatus,
    timeStatus: search.timeStatus,
    keyword: search.keyword,
    current: search.current,
    size: search.size
  });
  loading.value = false;
  if (!error && data) {
    tickets.value = data.records;
    total.value = data.total;
  }
}

const detailVisible = ref(false);
const detail = ref<Api.WorkTicketManagement.TicketDetail | null>(null);
function ticketRowKey(row: Api.WorkTicketManagement.Ticket) {
  return row.id;
}
function ticketRowProps(row: Api.WorkTicketManagement.Ticket) {
  return { onClick: () => openDetail(row) };
}
async function openDetail(row: Api.WorkTicketManagement.Ticket) {
  const { data } = await fetchTicket(row.id);
  if (data) {
    detail.value = data;
    detailVisible.value = true;
  }
}

const createVisible = ref(false);
const createSaving = ref(false);
const createForm = reactive({
  orderId: null as string | null,
  partNo: '',
  name: '',
  ticketCode: '',
  workerIds: [] as string[]
});
const orderPartNo = ref('');
const orderCandidates = ref<Api.WorkTicketManagement.OrderCandidate[]>([]);
const orderLoading = ref(false);
function openCreate() {
  Object.assign(createForm, { orderId: null, partNo: '', name: '', ticketCode: '', workerIds: [] });
  orderPartNo.value = '';
  orderCandidates.value = [];
  createVisible.value = true;
}
async function searchOrders() {
  if (!orderPartNo.value.trim()) return;
  const monthData = await ensureMonth();
  if (!monthData) return;
  orderLoading.value = true;
  const { data } = await fetchOrderCandidates({
    workMonthId: monthData.id,
    partNo: orderPartNo.value.trim(),
    includeOtherUnits: true,
    includePartial: true
  });
  orderLoading.value = false;
  orderCandidates.value = data ?? [];
}
async function submitCreate() {
  if (!createForm.orderId && !createForm.partNo.trim()) return;
  const monthData = await ensureMonth();
  if (!monthData) return;
  createSaving.value = true;
  const { error } = await fetchCreateTicket({
    workMonthId: monthData.id,
    orderId: createForm.orderId,
    partNoSnapshot: createForm.partNo || null,
    nameSnapshot: createForm.name || null,
    ticketCode: createForm.ticketCode || null,
    workerIds: createForm.workerIds,
    allowAddMapping: true
  });
  createSaving.value = false;
  if (error) return;
  createVisible.value = false;
  await load();
}

// The ledger must open the selected month before creating a ticket.
async function ensureMonth() {
  if (!unitId.value) return null;
  const { data, error } = await fetchOpenWorkMonth({ yearMonth: month.value, productionUnitId: unitId.value });
  if (error || !data) return null;
  return data;
}

const editCodeVisible = ref(false);
const editCode = ref('');
async function openEditCode() {
  if (!detail.value) return;
  editCode.value = detail.value.ticketCode || '';
  editCodeVisible.value = true;
}
async function submitEditCode() {
  if (!detail.value) return;
  const { data, error } = await fetchUpdateTicket(detail.value.id, {
    revision: detail.value.revision,
    ticketCode: editCode.value || null
  });
  if (error || !data) return;
  detail.value = data;
  editCodeVisible.value = false;
  await load();
}

const voidVisible = ref(false);
const voidReason = ref('');
async function submitVoid() {
  if (!detail.value || !voidReason.value.trim()) return;
  const { data, error } = await fetchVoidTicket(detail.value.id, detail.value.revision, voidReason.value.trim());
  if (error || !data) return;
  detail.value = data;
  voidVisible.value = false;
  voidReason.value = '';
  await load();
}

const assignVisible = ref(false);
const assignWorkerIds = ref<string[]>([]);
const assignAllowDisabled = ref(false);
function openSingleAssign() {
  assignWorkerIds.value = [];
  assignVisible.value = true;
}
const batchAssignVisible = ref(false);
const batchAssignWorkerIds = ref<string[]>([]);
const batchAssignAllowDisabled = ref(false);
function openBatchAssign() {
  batchAssignWorkerIds.value = [];
  batchAssignVisible.value = true;
}
async function submitBatchAssign() {
  if (!batchAssignWorkerIds.value.length || !checkedRowKeys.value.length) return;
  const { error } = await fetchBatchAssignTickets(checkedRowKeys.value, batchAssignWorkerIds.value, batchAssignAllowDisabled.value);
  if (error) return;
  batchAssignVisible.value = false;
  checkedRowKeys.value = [];
  await load();
}
async function submitAssign() {
  if (!detail.value) return;
  const { data, error } = await fetchAssignTicket(detail.value.id, detail.value.revision, assignWorkerIds.value, assignAllowDisabled.value);
  if (error || !data) return;
  detail.value = data;
  assignVisible.value = false;
  await load();
}
async function unassign(workerId: string) {
  if (!detail.value) return;
  const { data, error } = await fetchUnassignTicket(detail.value.id, detail.value.revision, workerId);
  if (error || !data) return;
  detail.value = data;
  await load();
}
async function markReconcile(status: 'checked' | 'ignored') {
  if (!detail.value) return;
  const { data, error } = await fetchReconcileTicket(detail.value.id, detail.value.revision, status, null);
  if (error || !data) return;
  detail.value = data;
  await load();
}

const ocrVisible = ref(false);
const ocrCandidates = ref<Api.WorkTicketManagement.OcrCandidate[]>([]);
const ocrSelected = ref<string[]>([]);
async function onOcrRecognized(result: Api.Ocr.Result) {
  const monthData = await ensureMonth();
  if (!monthData) return;
  const { data } = await fetchOcrCandidates(monthData.id, result.text, true);
  ocrCandidates.value = data ?? [];
}
async function applyOcr() {
  if (!ocrSelected.value.length || !checkedRowKeys.value.length) return;
  const selectedTickets = tickets.value.filter(ticket => checkedRowKeys.value.includes(ticket.id));
  const codes = [...ocrSelected.value];
  if (codes.length < selectedTickets.length) {
    window.$message?.warning($t('page.work_ticket_management.workflow.ticketCodeRequired'));
    return;
  }
  const items = selectedTickets.map((ticket, index) => ({ ticketId: ticket.id, revision: ticket.revision, code: codes[index] }));
  const { error } = await fetchPasteTicketCodes(items);
  if (error) return;
  ocrVisible.value = false;
  ocrSelected.value = [];
  ocrCandidates.value = [];
  checkedRowKeys.value = [];
  await load();
}

async function exportTickets() {
  const monthData = await ensureMonth();
  if (!monthData) return;
  const { data } = await fetchExportTickets({
    workMonthId: monthData.id,
    current: 1,
    size: 1
  });
  if (data) downloadExcel(data);
}

const columns: DataTableColumns<Api.WorkTicketManagement.Ticket> = [
  { type: 'selection', width: 44 },
  { key: 'ticketCode', title: $t('page.work_ticket_management.workflow.ticketCode'), minWidth: 130 },
  { key: 'partNoSnapshot', title: $t('page.work_ticket_management.workflow.partNo'), minWidth: 120 },
  { key: 'orderNoSnapshot', title: $t('page.work_ticket_management.workflow.orderNo'), minWidth: 130 },
  { key: 'nameSnapshot', title: $t('page.work_ticket_management.workflow.name'), minWidth: 150 },
  { key: 'status', title: $t('page.work_ticket_management.workflow.status'), width: 90, render: row => <StatusTag kind="ticket" value={row.status} /> },
  { key: 'workerNames', title: $t('page.work_ticket_management.workflow.assignment'), minWidth: 120, render: row => row.workerNames.join('、') || '—' },
  { key: 'totalHours', title: $t('page.work_ticket_management.workflow.totalHours'), width: 100 },
  { key: 'reconcileStatus', title: $t('page.work_ticket_management.workflow.reconcileStatus'), width: 100, render: row => <StatusTag kind="reconcile" value={row.reconcileStatus} /> }
];

watch([month, unitId], () => {
  search.current = 1;
  load();
});
onMounted(async () => {
  await loadUnits();
  if (!unitId.value && units.value.length) unitId.value = units.value[0].id;
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="card-wrapper">
      <NSpace align="center" wrap>
        <NDatePicker
          v-model:formatted-value="month"
          type="month"
          value-format="yyyy-MM"
          :clearable="false"
          class="w-150px"
        />
        <NSelect
          v-model:value="unitId"
          :options="units.map(unit => ({ label: unit.name, value: unit.id }))"
          filterable
          clearable
          class="w-220px"
        />
        <NInput
          v-model:value="search.keyword"
          clearable
          :placeholder="$t('page.work_ticket_management.workflow.keyword')"
          class="w-200px"
          @keyup.enter="load"
        />
        <NSelect
          v-model:value="search.status"
          :options="[
            { label: $t('page.work_ticket_management.workflow.active'), value: 'active' },
            { label: $t('page.work_ticket_management.workflow.void'), value: 'void' }
          ]"
          clearable
          class="w-120px"
        />
        <NSelect
          v-model:value="search.assignmentStatus"
          :options="[
            { label: $t('page.work_ticket_management.workflow.assigned'), value: 'assigned' },
            { label: $t('page.work_ticket_management.workflow.unassigned'), value: 'unassigned' },
            { label: $t('page.work_ticket_management.workflow.all'), value: 'all' }
          ]"
          class="w-130px"
        />
        <NSelect
          v-model:value="search.timeStatus"
          :options="[
            { label: $t('page.work_ticket_management.workflow.logged'), value: 'logged' },
            { label: $t('page.work_ticket_management.workflow.none'), value: 'none' },
            { label: $t('page.work_ticket_management.workflow.all'), value: 'all' }
          ]"
          class="w-130px"
        />
        <NButton size="small" @click="load">{{ $t('page.work_ticket_management.workflow.search') }}</NButton>
        <NButton size="small" :disabled="!checkedRowKeys.length" @click="openBatchAssign">
          {{ $t('page.work_ticket_management.workflow.assignWorkers') }}
        </NButton>
        <NButton size="small" :disabled="!checkedRowKeys.length" @click="ocrVisible = true">
          {{ $t('page.work_ticket_management.workflow.ocr') }}
        </NButton>
        <NButton size="small" @click="exportTickets">{{ $t('page.work_ticket_management.workflow.export') }}</NButton>
        <NButton
          size="small"
          type="primary"
          :disabled="!hasAuth('B_WORK_TICKET_MANAGEMENT_TICKET_CREATE')"
          @click="openCreate"
        >
          {{ $t('page.work_ticket_management.workflow.createTicket') }}
        </NButton>
      </NSpace>
    </NCard>

    <NCard :bordered="false" size="small" class="card-wrapper">
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="tickets"
        :loading="loading"
        :row-key="ticketRowKey"
        remote
        :pagination="{ page: search.current, pageSize: search.size, itemCount: total, showSizePicker: true, pageSizes: [20, 50, 100], onUpdatePage: (page: number) => { search.current = page; load(); }, onUpdatePageSize: (size: number) => { search.size = size; search.current = 1; load(); } }"
        size="small"
        :row-props="ticketRowProps"
      />
    </NCard>

    <NDrawer v-model:show="detailVisible" :width="720">
      <NDrawerContent :title="$t('page.work_ticket_management.workflow.ticketDetail')" closable>
        <template v-if="detail">
          <NDescriptions :column="2" bordered size="small">
            <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.ticketCode')">
              {{ detail.ticketCode || '—' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.status')">
              <StatusTag kind="ticket" :value="detail.status" />
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.partNo')">
              {{ detail.partNoSnapshot || '—' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.orderNo')">
              {{ detail.orderNoSnapshot || '—' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.name')">
              {{ detail.nameSnapshot || '—' }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.totalHours')">
              {{ detail.totalHours }}
            </NDescriptionsItem>
          </NDescriptions>
          <NSpace class="my-12px" wrap>
            <NButton size="small" :disabled="detail.status !== 'active'" @click="openEditCode">
              {{ $t('page.work_ticket_management.workflow.ticketCode') }}
            </NButton>
            <NButton size="small" :disabled="detail.status !== 'active'" @click="openSingleAssign">
              {{ $t('page.work_ticket_management.workflow.assignWorkers') }}
            </NButton>
            <NButton size="small" :disabled="detail.status !== 'active'" @click="markReconcile('checked')">
              {{ $t('page.work_ticket_management.workflow.checked') }}
            </NButton>
            <NButton size="small" :disabled="detail.status !== 'active'" @click="voidVisible = true">
              {{ $t('page.work_ticket_management.workflow.void') }}
            </NButton>
          </NSpace>
          <NDivider>{{ $t('page.work_ticket_management.workflow.assignment') }}</NDivider>
          <NList v-if="detail.assignments.length" bordered>
            <NListItem v-for="assignment in detail.assignments" :key="assignment.id">
              <div class="flex items-center justify-between gap-8px">
                <span>
                  {{ assignment.workerName }}
                  {{ assignment.workerEnabled ? '' : `(${$t('page.work_ticket_management.workflow.disabled')})` }}
                </span>
                <NPopconfirm @positive-click="unassign(assignment.workerId)">
                  <template #trigger>
                    <NButton size="tiny" type="error" ghost>
                      {{ $t('page.work_ticket_management.workflow.delete') }}
                    </NButton>
                  </template>
                  {{ $t('common.confirmDelete') }}
                </NPopconfirm>
              </div>
            </NListItem>
          </NList>
          <NEmpty v-else :description="$t('page.work_ticket_management.workflow.unassigned')" />
          <NDivider>{{ $t('page.work_ticket_management.workflow.time') }}</NDivider>
          <NDataTable
            :columns="[
              { key: 'workerName', title: $t('page.work_ticket_management.workflow.worker') },
              { key: 'workDate', title: $t('page.work_ticket_management.workflow.workDate') },
              { key: 'accountingMonth', title: $t('page.work_ticket_management.workflow.accountingMonth') },
              { key: 'hours', title: $t('page.work_ticket_management.workflow.hours') }
            ]"
            :data="detail.timeEntries"
            size="small"
          />
        </template>
      </NDrawerContent>
    </NDrawer>

    <NModal
      v-model:show="createVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.createTicket')"
      class="w-680px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.workflow.orderNo')">
          <NSpace vertical class="w-full">
            <NInput
              v-model:value="orderPartNo"
              :placeholder="$t('page.work_ticket_management.workflow.partNo')"
              @keyup.enter="searchOrders"
            />
            <NButton size="small" :loading="orderLoading" @click="searchOrders">
              {{ $t('page.work_ticket_management.workflow.search') }}
            </NButton>
            <NSelect
              v-model:value="createForm.orderId"
              :options="
                orderCandidates.map(order => ({
                  label: `${order.partNo} | ${order.orderNo} | ${order.name}`,
                  value: order.id
                }))
              "
              clearable
              filterable
            />
          </NSpace>
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.partNo')">
          <NInput v-model:value="createForm.partNo" :disabled="Boolean(createForm.orderId)" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.name')">
          <NInput v-model:value="createForm.name" :disabled="Boolean(createForm.orderId)" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.ticketCode')">
          <NInput v-model:value="createForm.ticketCode" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.assignWorkers')">
          <WorkerSelect v-model:value="createForm.workerIds" :production-unit-id="unitId" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="createVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="createSaving" @click="submitCreate">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="editCodeVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.ticketCode')"
      class="w-500px max-w-95vw"
    >
      <NInput v-model:value="editCode" />
      <template #footer>
        <NSpace justify="end">
          <NButton @click="editCodeVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitEditCode">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="assignVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.assignWorkers')"
      class="w-520px max-w-95vw"
    >
      <NSpace vertical>
        <NCheckbox v-model:checked="assignAllowDisabled">
          {{ $t('page.work_ticket_management.workflow.disabled') }}
        </NCheckbox>
        <WorkerSelect
          v-model:value="assignWorkerIds"
          :production-unit-id="unitId"
          :include-disabled="assignAllowDisabled"
        />
      </NSpace>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="assignVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitAssign">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="voidVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.void')"
      class="w-500px max-w-95vw"
    >
      <NInput
        v-model:value="voidReason"
        type="textarea"
        :placeholder="$t('page.work_ticket_management.workflow.remark')"
      />
      <template #footer>
        <NSpace justify="end">
          <NButton @click="voidVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitVoid">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="batchAssignVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.assignWorkers')"
      class="w-520px max-w-95vw"
    >
      <NSpace vertical>
        <NCheckbox v-model:checked="batchAssignAllowDisabled">
          {{ $t('page.work_ticket_management.workflow.disabled') }}
        </NCheckbox>
        <WorkerSelect
          v-model:value="batchAssignWorkerIds"
          :production-unit-id="unitId"
          :include-disabled="batchAssignAllowDisabled"
        />
      </NSpace>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="batchAssignVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitBatchAssign">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="ocrVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.ocrCandidates')"
      class="w-760px max-w-95vw"
    >
      <OcrRecognizer :max-size-mb="10" @recognized="onOcrRecognized" />
      <NCheckboxGroup v-if="ocrCandidates.length" v-model:value="ocrSelected" class="mt-12px">
        <NSpace vertical>
          <NCheckbox
            v-for="candidate in ocrCandidates"
            :key="candidate.normalized"
            :value="candidate.normalized"
            :label="`${candidate.original} → ${candidate.normalized}`"
          />
        </NSpace>
      </NCheckboxGroup>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="ocrVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" :disabled="!ocrSelected.length || !checkedRowKeys.length" @click="applyOcr">
            {{ $t('page.work_ticket_management.workflow.pasteCodes') }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>
