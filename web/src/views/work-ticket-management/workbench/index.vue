<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import type { DataTableColumns, UploadCustomRequestOptions } from 'naive-ui';
import { NButton, NPopconfirm, NSpace, NTag } from 'naive-ui';
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';
import {
  downloadExcel
} from '@/utils/excel';
import {
  fetchAssignTicket,
  fetchBatchMatchImportRows,
  fetchCloseWorkMonth,
  fetchCodeConfirm,
  fetchCodePreview,
  fetchCreateTicket,
  fetchExportWorkMonthWorkbook,
  fetchIgnoreImportRow,
  fetchImportCommit,
  fetchImportPreview,
  fetchImportRows,
  fetchManualImport,
  fetchMatchImportRow,
  fetchOcrCandidates,
  fetchOpenWorkMonth,
  fetchOrderCandidates,
  fetchProductionUnitOptions,
  fetchReopenWorkMonth,
  fetchTickets,
  fetchTicket,
  fetchVerifyWorkMonth,
  fetchWorkMonthStatusLogs,
  fetchWorkMonthSummary
} from '@/service/api';
import { $t } from '@/locales';
import MonthUnitToolbar from '../shared/month-unit-toolbar.vue';
import StatusTag from '../shared/status-tag.vue';
import WorkerSelect from '../shared/worker-select.vue';

defineOptions({ name: 'WorkTicketWorkbench' });

const month = ref(dayjs().format('YYYY-MM'));
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const unitId = ref<string | null>(null);
const summary = ref<Api.WorkTicketManagement.WorkMonthSummary | null>(null);
const monthLoading = ref(false);
const tab = ref<'rows' | 'tickets'>('rows');

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
  if (!unitId.value && units.value.length) unitId.value = units.value[0].id;
}
async function openMonth() {
  if (!unitId.value) return;
  monthLoading.value = true;
  const { data, error } = await fetchOpenWorkMonth({ yearMonth: month.value, productionUnitId: unitId.value });
  monthLoading.value = false;
  if (error || !data) return;
  summary.value = data;
  await Promise.all([loadRows(), loadTickets()]);
}
async function loadSummary() {
  if (!summary.value) return;
  const { data } = await fetchWorkMonthSummary(summary.value.id);
  if (data) summary.value = data;
}

const rows = ref<Api.WorkTicketManagement.ImportRow[]>([]);
const rowLoading = ref(false);
const rowSource = ref<Api.WorkTicketManagement.ImportSourceType | null>(null);
const rowStatus = ref<Api.WorkTicketManagement.MatchStatus | null>(null);
const rowKeyword = ref('');
const rowPage = reactive({ page: 1, pageSize: 20, itemCount: 0 });
const selectedRow = ref<Api.WorkTicketManagement.ImportRow | null>(null);
const selectedRowKeys = ref<string[]>([]);

async function loadRows() {
  if (!summary.value) return;
  rowLoading.value = true;
  const { data, error } = await fetchImportRows({
    workMonthId: summary.value.id,
    sourceType: rowSource.value,
    matchStatus: rowStatus.value,
    keyword: rowKeyword.value || null,
    current: rowPage.page,
    size: rowPage.pageSize
  });
  rowLoading.value = false;
  if (!error && data) {
    rows.value = data.records;
    rowPage.itemCount = data.total;
  }
}

const tickets = ref<Api.WorkTicketManagement.Ticket[]>([]);
const ticketLoading = ref(false);
const ticketPage = reactive({ page: 1, pageSize: 20, itemCount: 0 });
const selectedTicket = ref<Api.WorkTicketManagement.TicketDetail | null>(null);

async function loadTickets() {
  if (!summary.value) return;
  ticketLoading.value = true;
  const { data, error } = await fetchTickets({
    workMonthId: summary.value.id,
    current: ticketPage.page,
    size: ticketPage.pageSize
  });
  ticketLoading.value = false;
  if (!error && data) {
    tickets.value = data.records;
    ticketPage.itemCount = data.total;
  }
}

function importRowKey(row: Api.WorkTicketManagement.ImportRow) {
  return row.id;
}
function importRowProps(row: Api.WorkTicketManagement.ImportRow) {
  return { onClick: () => selectRow(row) };
}
function ticketRowKey(row: Api.WorkTicketManagement.Ticket) {
  return row.id;
}
function ticketRowProps(row: Api.WorkTicketManagement.Ticket) {
  return { onClick: () => selectTicket(row) };
}
async function selectRow(row: Api.WorkTicketManagement.ImportRow) {
  selectedRow.value = row;
  selectedTicket.value = null;
  await loadCandidates(row);
}

const candidates = ref<Api.WorkTicketManagement.OrderCandidate[]>([]);
const candidateLoading = ref(false);
const includeOtherUnits = ref(false);
const includePartial = ref(false);

async function loadCandidates(row: Api.WorkTicketManagement.ImportRow) {
  if (!summary.value) return;
  candidateLoading.value = true;
  const { data } = await fetchOrderCandidates({
    workMonthId: summary.value.id,
    partNo: row.normalizedPartNo || row.rawPartNo,
    includeOtherUnits: includeOtherUnits.value,
    includePartial: includePartial.value
  });
  candidateLoading.value = false;
  candidates.value = data ?? [];
}

async function matchOrder(candidate: Api.WorkTicketManagement.OrderCandidate) {
  if (!selectedRow.value) return;
  const { error } = await fetchMatchImportRow(selectedRow.value.id, candidate.id, true);
  if (error) return;
  await Promise.all([loadRows(), loadSummary()]);
  selectedRow.value = null;
  candidates.value = [];
}

const ignoreVisible = ref(false);
const ignoreReason = ref('');
const ignoringRow = ref<Api.WorkTicketManagement.ImportRow | null>(null);
function openIgnore(row: Api.WorkTicketManagement.ImportRow) {
  ignoringRow.value = row;
  ignoreReason.value = '';
  ignoreVisible.value = true;
}
async function submitIgnore() {
  if (!ignoringRow.value || !ignoreReason.value.trim()) return;
  const { error } = await fetchIgnoreImportRow(ignoringRow.value.id, ignoreReason.value.trim());
  if (error) return;
  ignoreVisible.value = false;
  await Promise.all([loadRows(), loadSummary()]);
}

// ---- import ----
const importVisible = ref(false);
const importSource = ref<Api.WorkTicketManagement.ImportSourceType>('plan');
const importFile = ref<File | null>(null);
const importPreview = ref<Api.WorkTicketManagement.ImportPreview | null>(null);
const importCommitting = ref(false);
const importPreviewLoading = ref(false);
function openImport(source: Api.WorkTicketManagement.ImportSourceType) {
  importSource.value = source;
  importFile.value = null;
  importPreview.value = null;
  importVisible.value = true;
}
async function previewFile(options: UploadCustomRequestOptions) {
  const file = options.file.file;
  if (!file || !summary.value) {
    options.onError();
    return;
  }
  importPreviewLoading.value = true;
  const { data, error } = await fetchImportPreview(file, summary.value.id, importSource.value);
  importPreviewLoading.value = false;
  if (error || !data) {
    options.onError();
    return;
  }
  importFile.value = file;
  importPreview.value = data;
  options.onFinish();
}
async function commitImport() {
  if (!importFile.value || !summary.value) return;
  importCommitting.value = true;
  const { error } = await fetchImportCommit(importFile.value, summary.value.id, importSource.value);
  importCommitting.value = false;
  if (error) return;
  importVisible.value = false;
  await Promise.all([loadRows(), loadTickets(), loadSummary()]);
}

const manualVisible = ref(false);
const manualText = ref('');
async function submitManual() {
  if (!summary.value) return;
  const lines = manualText.value
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);
  if (!lines.length) return;
  const { error } = await fetchManualImport({
    workMonthId: summary.value.id,
    sourceType: importSource.value,
    rows: lines.map(rawPartNo => ({ rawPartNo }))
  });
  if (error) return;
  manualVisible.value = false;
  manualText.value = '';
  await Promise.all([loadRows(), loadSummary()]);
}

async function batchMatch() {
  if (!summary.value) return;
  await fetchBatchMatchImportRows(summary.value.id, selectedRowKeys.value.length ? selectedRowKeys.value : undefined);
  selectedRowKeys.value = [];
  await Promise.all([loadRows(), loadSummary()]);
}

// ---- ticket create ----
const ticketVisible = ref(false);
const ticketSaving = ref(false);
const ticketForm = reactive({ code: '', workerIds: [] as string[] });
function openTicketCreate() {
  if (!selectedRow.value) return;
  ticketForm.code = '';
  ticketForm.workerIds = [];
  ticketVisible.value = true;
}
async function submitTicket() {
  if (!summary.value || !selectedRow.value) return;
  ticketSaving.value = true;
  const { error } = await fetchCreateTicket({
    workMonthId: summary.value.id,
    orderId: selectedRow.value.orderId,
    sourceImportRowId: selectedRow.value.id,
    partNoSnapshot: selectedRow.value.normalizedPartNo,
    ticketCode: ticketForm.code || null,
    workerIds: ticketForm.workerIds,
    allowAddMapping: true
  });
  ticketSaving.value = false;
  if (error) return;
  ticketVisible.value = false;
  selectedRow.value = null;
  await Promise.all([loadRows(), loadTickets(), loadSummary()]);
}

// ---- code preview ----
const codeVisible = ref(false);
const codeLoading = ref(false);
const codePreview = ref<Api.WorkTicketManagement.CodePreview | null>(null);
const codeInputs = reactive<Record<number, string>>({});
async function openCodePreview() {
  if (!summary.value) return;
  const chosen = rows.value.filter(row => selectedRowKeys.value.includes(row.id) && (row.orderId || row.matchStatus === 'matched'));
  if (!chosen.length) {
    window.$message?.warning($t('page.work_ticket_management.workflow.ticketCodeRequired'));
    return;
  }
  codeVisible.value = true;
  codeLoading.value = true;
  const { data } = await fetchCodePreview({
    workMonthId: summary.value.id,
    items: chosen.map(row => ({ orderId: row.orderId, sourceImportRowId: row.id }))
  });
  codeLoading.value = false;
  codePreview.value = data;
  Object.keys(codeInputs).forEach(key => Reflect.deleteProperty(codeInputs, key));
}
async function submitCodes() {
  if (!summary.value || !codePreview.value) return;
  const items = codePreview.value.rows.map((row, index) => ({
    orderId: row.orderId,
    sourceImportRowId: row.sourceImportRowId,
    code: codeInputs[index] || row.previewCode
  }));
  if (items.some(item => !item.code)) {
    window.$message?.warning($t('page.work_ticket_management.workflow.ticketCodeRequired'));
    return;
  }
  codeLoading.value = true;
  const { data, error } = await fetchCodeConfirm({
    workMonthId: summary.value.id,
    allowAddMapping: true,
    items
  });
  codeLoading.value = false;
  if (error || !data) return;
  codeVisible.value = false;
  selectedRowKeys.value = [];
  await Promise.all([loadRows(), loadTickets(), loadSummary()]);
}

// ---- ticket detail / assign ----
async function selectTicket(row: Api.WorkTicketManagement.Ticket) {
  selectedRow.value = null;
  candidates.value = [];
  const { data } = await fetchTicket(row.id);
  selectedTicket.value = data;
}
const assignVisible = ref(false);
const assignWorkerIds = ref<string[]>([]);
const assignAllowDisabled = ref(false);
async function submitAssign() {
  if (!selectedTicket.value) return;
  const { data, error } = await fetchAssignTicket(
    selectedTicket.value.id,
    selectedTicket.value.revision,
    assignWorkerIds.value,
    assignAllowDisabled.value
  );
  if (error || !data) return;
  selectedTicket.value = data;
  assignVisible.value = false;
  await loadTickets();
}

// ---- month actions ----
async function verifyMonth() {
  if (!summary.value) return;
  const { data, error } = await fetchVerifyWorkMonth(summary.value.id, { revision: summary.value.revision });
  if (!error && data) summary.value = data;
  await loadSummary();
}
async function closeMonth() {
  if (!summary.value) return;
  const { data, error } = await fetchCloseWorkMonth(summary.value.id, { revision: summary.value.revision, confirmWarnings: true });
  if (!error && data) summary.value = data;
  await loadSummary();
}
const reopenVisible = ref(false);
const reopenReason = ref('');
async function submitReopen() {
  if (!summary.value || !reopenReason.value.trim()) return;
  const { data, error } = await fetchReopenWorkMonth(summary.value.id, {
    revision: summary.value.revision,
    reason: reopenReason.value.trim()
  });
  if (error || !data) return;
  summary.value = data;
  reopenVisible.value = false;
  reopenReason.value = '';
  await loadSummary();
}
async function exportMonth() {
  if (!summary.value) return;
  const { data } = await fetchExportWorkMonthWorkbook(summary.value.id);
  if (data) downloadExcel(data);
}

// ---- audit ----
const statusLogsVisible = ref(false);
const statusLogsLoading = ref(false);
const statusLogs = ref<Api.WorkTicketManagement.StatusLog[]>([]);
async function openStatusLogs() {
  if (!summary.value) return;
  statusLogsVisible.value = true;
  statusLogsLoading.value = true;
  const { data } = await fetchWorkMonthStatusLogs(summary.value.id);
  statusLogsLoading.value = false;
  statusLogs.value = data ?? [];
}
const statusLogColumns: DataTableColumns<Api.WorkTicketManagement.StatusLog> = [
  { key: 'createdAt', title: $t('page.work_ticket_management.workflow.createdAt'), width: 170 },
  {
    key: 'fromStatus',
    title: $t('page.work_ticket_management.workflow.fromStatus'),
    width: 110,
    render: (row: Api.WorkTicketManagement.StatusLog) => (row.fromStatus ? <StatusTag kind="month" value={row.fromStatus} /> : '—')
  },
  {
    key: 'toStatus',
    title: $t('page.work_ticket_management.workflow.toStatus'),
    width: 110,
    render: (row: Api.WorkTicketManagement.StatusLog) => <StatusTag kind="month" value={row.toStatus} />
  },
  { key: 'action', title: $t('page.work_ticket_management.workflow.action'), width: 100 },
  { key: 'reason', title: $t('page.work_ticket_management.workflow.reason'), minWidth: 200 },
  { key: 'createdBy', title: $t('page.work_ticket_management.workflow.createdBy'), width: 120 }
];

// ---- OCR ----
const ocrVisible = ref(false);
const ocrCandidates = ref<Api.WorkTicketManagement.OcrCandidate[]>([]);
function openOcr() {
  ocrCandidates.value = [];
  ocrVisible.value = true;
}
async function onOcrRecognized(result: Api.Ocr.Result) {
  if (!summary.value) return;
  const { data } = await fetchOcrCandidates(summary.value.id, result.text, true);
  ocrCandidates.value = data ?? [];
}

const monthStatus = computed(() => summary.value?.status ?? null);
const readonlyMonth = computed(() => monthStatus.value === 'verified' || monthStatus.value === 'closed');

watch([month, unitId], () => {
  summary.value = null;
  rows.value = [];
  tickets.value = [];
  selectedRow.value = null;
  selectedTicket.value = null;
  if (month.value && unitId.value) openMonth();
});
watch(tab, () => {
  if (tab.value === 'rows') loadRows();
  else loadTickets();
});
onMounted(loadUnits);

const rowColumns: DataTableColumns<Api.WorkTicketManagement.ImportRow> = [
  { type: 'selection', width: 44 },
  { key: 'rawPartNo', title: $t('page.work_ticket_management.workflow.partNo'), minWidth: 130 },
  { key: 'sourceType', title: $t('page.work_ticket_management.workflow.sourceType'), width: 100, render: (row: Api.WorkTicketManagement.ImportRow) => (row.sourceType === 'actual' ? $t('page.work_ticket_management.workflow.actual') : $t('page.work_ticket_management.workflow.plan')) },
  { key: 'matchStatus', title: $t('page.work_ticket_management.workflow.matchStatus'), width: 110, render: (row: Api.WorkTicketManagement.ImportRow) => <StatusTag kind="match" value={row.matchStatus} /> },
  { key: 'orderNo', title: $t('page.work_ticket_management.workflow.orderNo'), minWidth: 130, render: (row: Api.WorkTicketManagement.ImportRow) => row.orderNo || '—' },
  { key: 'name', title: $t('page.work_ticket_management.workflow.name'), minWidth: 150, render: (row: Api.WorkTicketManagement.ImportRow) => row.name || '—' },
  { key: 'handlingStatus', title: $t('page.work_ticket_management.workflow.handling'), width: 100, render: (row: Api.WorkTicketManagement.ImportRow) => <StatusTag kind="handling" value={row.handlingStatus} /> },
  { key: 'duplicate', title: $t('page.work_ticket_management.workflow.duplicate'), width: 80, render: (row: Api.WorkTicketManagement.ImportRow) => (row.duplicateOfRowId ? <NTag size="small" type="warning">{ $t('page.work_ticket_management.workflow.duplicate') }</NTag> : '—') }
];

const ticketColumns: DataTableColumns<Api.WorkTicketManagement.Ticket> = [
  { key: 'ticketCode', title: $t('page.work_ticket_management.workflow.ticketCode'), minWidth: 130 },
  { key: 'partNoSnapshot', title: $t('page.work_ticket_management.workflow.partNo'), minWidth: 120 },
  { key: 'orderNoSnapshot', title: $t('page.work_ticket_management.workflow.orderNo'), minWidth: 130 },
  { key: 'status', title: $t('page.work_ticket_management.workflow.status'), width: 90, render: (row: Api.WorkTicketManagement.Ticket) => <StatusTag kind="ticket" value={row.status} /> },
  { key: 'assignmentCount', title: $t('page.work_ticket_management.workflow.assignment'), width: 90 },
  { key: 'totalHours', title: $t('page.work_ticket_management.workflow.totalHours'), width: 100 },
  { key: 'reconcileStatus', title: $t('page.work_ticket_management.workflow.reconcileStatus'), width: 100, render: (row: Api.WorkTicketManagement.Ticket) => <StatusTag kind="reconcile" value={row.reconcileStatus} /> }
];
const codeColumns: DataTableColumns<Api.WorkTicketManagement.CodePreviewRow> = [
  { key: 'partNo', title: $t('page.work_ticket_management.workflow.partNo') },
  { key: 'orderNo', title: $t('page.work_ticket_management.workflow.orderNo') },
  {
    key: 'previewCode',
    title: $t('page.work_ticket_management.workflow.ticketCode'),
    render: (row: Api.WorkTicketManagement.CodePreviewRow, index: number) => (
      <NInput
        value={codeInputs[index] ?? row.previewCode ?? ''}
        onUpdateValue={(value: string) => {
          codeInputs[index] = value;
        }}
      />
    )
  },
  {
    key: 'error',
    title: $t('page.work_ticket_management.workflow.status'),
    render: (row: Api.WorkTicketManagement.CodePreviewRow) => row.error || '—'
  }
];
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <MonthUnitToolbar
      v-model:month="month"
      v-model:unit-id="unitId"
      :units="units"
      :status="monthStatus"
      :loading="monthLoading"
    >
      <NButton size="small" type="primary" :loading="monthLoading" @click="openMonth">
        {{ $t('page.work_ticket_management.workflow.openMonth') }}
      </NButton>
      <NButton size="small" :disabled="readonlyMonth" @click="openImport('plan')">
        {{ $t('page.work_ticket_management.workflow.importPlan') }}
      </NButton>
      <NButton size="small" :disabled="readonlyMonth" @click="openImport('actual')">
        {{ $t('page.work_ticket_management.workflow.importActual') }}
      </NButton>
      <NButton size="small" :disabled="readonlyMonth" @click="manualVisible = true">
        {{ $t('page.work_ticket_management.workflow.manualImport') }}
      </NButton>
      <NButton size="small" :disabled="readonlyMonth" @click="openCodePreview">
        {{ $t('page.work_ticket_management.workflow.generateCodes') }}
      </NButton>
      <NButton size="small" @click="openOcr">{{ $t('page.work_ticket_management.workflow.ocr') }}</NButton>
      <NButton size="small" @click="exportMonth">{{ $t('page.work_ticket_management.workflow.export') }}</NButton>
      <NButton size="small" :disabled="!summary" @click="openStatusLogs">
        {{ $t('page.work_ticket_management.workflow.statusLogs') }}
      </NButton>
      <NPopconfirm @positive-click="verifyMonth">
        <template #trigger>
          <NButton size="small" :disabled="readonlyMonth || monthStatus !== 'in_progress'">
            {{ $t('page.work_ticket_management.workflow.verifyMonth') }}
          </NButton>
        </template>
        {{ $t('common.confirm') }}
      </NPopconfirm>
      <NPopconfirm @positive-click="closeMonth">
        <template #trigger>
          <NButton size="small" :disabled="monthStatus !== 'verified'">
            {{ $t('page.work_ticket_management.workflow.closeMonth') }}
          </NButton>
        </template>
        {{ $t('page.work_ticket_management.workflow.closeWarnings') }}
      </NPopconfirm>
      <NButton size="small" :disabled="!readonlyMonth" @click="reopenVisible = true">
        {{ $t('page.work_ticket_management.workflow.reopenMonth') }}
      </NButton>
    </MonthUnitToolbar>

    <NAlert v-if="summary && !summary.hasActualBatch" type="warning" :show-icon="true">
      {{ $t('page.work_ticket_management.workflow.actualNotReconciled') }}
    </NAlert>

    <NGrid v-if="summary" cols="1 s:2 m:3 l:6" responsive="screen" :x-gap="12" :y-gap="12">
      <NGi><NStatistic :label="$t('page.work_ticket_management.workflow.statsTotal')" :value="summary.rowCount" /></NGi>
      <NGi>
        <NStatistic :label="$t('page.work_ticket_management.workflow.statsMatched')" :value="summary.matchedRows" />
      </NGi>
      <NGi>
        <NStatistic :label="$t('page.work_ticket_management.workflow.statsTickets')" :value="summary.ticketCount" />
      </NGi>
      <NGi>
        <NStatistic
          :label="$t('page.work_ticket_management.workflow.statsUnassigned')"
          :value="summary.ticketCount - summary.assignedTicketCount"
        />
      </NGi>
      <NGi>
        <NStatistic
          :label="$t('page.work_ticket_management.workflow.statsNoTime')"
          :value="summary.ticketCount - summary.timedTicketCount"
        />
      </NGi>
      <NGi>
        <NStatistic :label="$t('page.work_ticket_management.workflow.statsAnomalies')" :value="summary.anomalyCount" />
      </NGi>
    </NGrid>

    <NGrid v-if="summary" cols="1 l:3" responsive="screen" :x-gap="16">
      <NGi span="1 l:2">
        <NCard :bordered="false" size="small" class="card-wrapper">
          <NTabs v-model:value="tab" type="line">
            <NTabPane name="rows" :tab="$t('page.work_ticket_management.workflow.importRows')">
              <NSpace class="mb-12px" align="center" wrap>
                <NSelect
                  v-model:value="rowSource"
                  :options="[
                    { label: $t('page.work_ticket_management.workflow.plan'), value: 'plan' },
                    { label: $t('page.work_ticket_management.workflow.actual'), value: 'actual' }
                  ]"
                  clearable
                  class="w-130px"
                  @update:value="loadRows"
                />
                <NSelect
                  v-model:value="rowStatus"
                  :options="[
                    { label: $t('page.work_ticket_management.workflow.matched'), value: 'matched' },
                    { label: $t('page.work_ticket_management.workflow.ambiguous'), value: 'ambiguous' },
                    { label: $t('page.work_ticket_management.workflow.unassigned'), value: 'unassigned' },
                    { label: $t('page.work_ticket_management.workflow.missing'), value: 'missing' }
                  ]"
                  clearable
                  class="w-130px"
                  @update:value="loadRows"
                />
                <NInput
                  v-model:value="rowKeyword"
                  clearable
                  :placeholder="$t('page.work_ticket_management.workflow.keyword')"
                  class="w-200px"
                  @keyup.enter="loadRows"
                />
                <NButton size="small" @click="loadRows">
                  {{ $t('page.work_ticket_management.workflow.search') }}
                </NButton>
                <NButton size="small" :disabled="!selectedRowKeys.length" @click="batchMatch">
                  {{ $t('page.work_ticket_management.workflow.batchMatch') }}
                </NButton>
              </NSpace>
              <NDataTable
                v-model:checked-row-keys="selectedRowKeys"
                :columns="rowColumns"
                :data="rows"
                :loading="rowLoading"
                :row-key="importRowKey"
                size="small"
                remote
                :pagination="{ page: rowPage.page, pageSize: rowPage.pageSize, itemCount: rowPage.itemCount, showSizePicker: true, pageSizes: [20, 50, 100], onUpdatePage: (page: number) => { rowPage.page = page; loadRows(); }, onUpdatePageSize: (size: number) => { rowPage.pageSize = size; rowPage.page = 1; loadRows(); } }"
                :row-props="importRowProps"
              />
            </NTabPane>
            <NTabPane name="tickets" :tab="$t('page.work_ticket_management.workflow.monthTickets')">
              <NDataTable
                :columns="ticketColumns"
                :data="tickets"
                :loading="ticketLoading"
                :row-key="ticketRowKey"
                size="small"
                remote
                :pagination="{ page: ticketPage.page, pageSize: ticketPage.pageSize, itemCount: ticketPage.itemCount, onUpdatePage: (page: number) => { ticketPage.page = page; loadTickets(); } }"
                :row-props="ticketRowProps"
              />
            </NTabPane>
          </NTabs>
        </NCard>
      </NGi>
      <NGi>
        <NCard :bordered="false" size="small" class="card-wrapper">
          <template #header>
            {{
              selectedTicket
                ? $t('page.work_ticket_management.workflow.ticketDetail')
                : $t('page.work_ticket_management.workflow.candidateOrders')
            }}
          </template>
          <NEmpty
            v-if="!selectedRow && !selectedTicket"
            :description="$t('page.work_ticket_management.workflow.selectRowHint')"
          />
          <template v-else-if="selectedRow">
            <NDescriptions :column="1" bordered size="small">
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.partNo')">
                {{ selectedRow.rawPartNo }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.status')">
                <StatusTag kind="match" :value="selectedRow.matchStatus" />
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.orderNo')">
                {{ selectedRow.orderNo || '—' }}
              </NDescriptionsItem>
            </NDescriptions>
            <NSpace class="my-12px" align="center" wrap>
              <NCheckbox
                v-model:checked="includeOtherUnits"
                @update:checked="() => selectedRow && loadCandidates(selectedRow)"
              >
                {{ $t('page.work_ticket_management.workflow.includeOtherUnits') }}
              </NCheckbox>
              <NCheckbox
                v-model:checked="includePartial"
                @update:checked="() => selectedRow && loadCandidates(selectedRow)"
              >
                {{ $t('page.work_ticket_management.workflow.includePartial') }}
              </NCheckbox>
            </NSpace>
            <NSpin :show="candidateLoading">
              <NEmpty
                v-if="!candidates.length"
                :description="$t('page.work_ticket_management.workflow.noCandidates')"
              />
              <NList v-else bordered>
                <NListItem v-for="candidate in candidates" :key="candidate.id">
                  <div class="flex items-center justify-between gap-8px">
                    <div class="min-w-0">
                      <div class="text-14px">{{ candidate.partNo }} · {{ candidate.orderNo }}</div>
                      <div class="text-12px text-gray-500">{{ candidate.name }} · {{ candidate.mappingStatus }}</div>
                    </div>
                    <NButton size="small" type="primary" @click="matchOrder(candidate)">
                      {{ $t('page.work_ticket_management.workflow.confirmOrder') }}
                    </NButton>
                  </div>
                </NListItem>
              </NList>
            </NSpin>
            <NSpace class="mt-12px" wrap>
              <NButton size="small" type="primary" :disabled="!selectedRow.orderId" @click="openTicketCreate">
                {{ $t('page.work_ticket_management.workflow.createTicket') }}
              </NButton>
              <NButton size="small" @click="openIgnore(selectedRow)">
                {{ $t('page.work_ticket_management.workflow.ignore') }}
              </NButton>
            </NSpace>
          </template>
          <template v-else-if="selectedTicket">
            <NDescriptions :column="1" bordered size="small">
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.ticketCode')">
                {{ selectedTicket.ticketCode || '—' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.partNo')">
                {{ selectedTicket.partNoSnapshot || '—' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.orderNo')">
                {{ selectedTicket.orderNoSnapshot || '—' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.assignment')">
                {{ selectedTicket.workerNames.join('、') || '—' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.totalHours')">
                {{ selectedTicket.totalHours }}
              </NDescriptionsItem>
            </NDescriptions>
            <NSpace class="mt-12px">
              <NButton size="small" type="primary" :disabled="readonlyMonth" @click="assignVisible = true">
                {{ $t('page.work_ticket_management.workflow.assignWorkers') }}
              </NButton>
            </NSpace>
          </template>
        </NCard>
      </NGi>
    </NGrid>

    <NModal
      v-model:show="importVisible"
      preset="card"
      :title="
        importSource === 'actual'
          ? $t('page.work_ticket_management.workflow.importActual')
          : $t('page.work_ticket_management.workflow.importPlan')
      "
      class="w-900px max-w-95vw"
    >
      <NSpace vertical :size="12">
        <NUpload accept=".xlsx" :show-file-list="false" :custom-request="previewFile">
          <NButton :loading="importPreviewLoading">{{ $t('page.work_ticket_management.workflow.import') }}</NButton>
        </NUpload>
        <NAlert v-if="importPreview?.errors.length" type="warning">
          <div v-for="(error, index) in importPreview.errors" :key="index">{{ error }}</div>
        </NAlert>
        <NDescriptions v-if="importPreview" :column="4" bordered size="small">
          <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.statsTotal')">
            {{ importPreview.totalRows }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.matched')">
            {{ importPreview.matchedRows }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.ambiguous')">
            {{ importPreview.ambiguousRows }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.missing')">
            {{ importPreview.missingRows }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.invalid')">
            {{ importPreview.invalidRows }}
          </NDescriptionsItem>
          <NDescriptionsItem :label="$t('page.work_ticket_management.workflow.duplicate')">
            {{ importPreview.duplicateRows }}
          </NDescriptionsItem>
        </NDescriptions>
        <NAlert v-if="importPreview?.truncated" type="info">
          {{ $t('page.work_ticket_management.workflow.previewTruncated') }}
        </NAlert>
        <NDataTable
          v-if="importPreview"
          :columns="[
            { key: 'rawPartNo', title: $t('page.work_ticket_management.workflow.partNo') },
            { key: 'matchStatus', title: $t('page.work_ticket_management.workflow.matchStatus') },
            { key: 'orderNo', title: $t('page.work_ticket_management.workflow.orderNo') },
            { key: 'note', title: $t('page.work_ticket_management.workflow.remark') }
          ]"
          :data="importPreview.rows"
          size="small"
          :max-height="360"
        />
      </NSpace>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="importVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton
            type="primary"
            :loading="importCommitting"
            :disabled="!importPreview || Boolean(importPreview.errors.length)"
            @click="commitImport"
          >
            {{ $t('page.work_ticket_management.workflow.importConfirm') }}
          </NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="manualVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.manualImport')"
      class="w-600px max-w-95vw"
    >
      <NSelect
        v-model:value="importSource"
        :options="[
          { label: $t('page.work_ticket_management.workflow.plan'), value: 'plan' },
          { label: $t('page.work_ticket_management.workflow.actual'), value: 'actual' }
        ]"
        class="mb-12px"
      />
      <NInput
        v-model:value="manualText"
        type="textarea"
        :autosize="{ minRows: 8, maxRows: 20 }"
        :placeholder="$t('page.work_ticket_management.workflow.partNo')"
      />
      <template #footer>
        <NSpace justify="end">
          <NButton @click="manualVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitManual">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="ticketVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.createTicket')"
      class="w-560px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.workflow.ticketCode')">
          <NInput v-model:value="ticketForm.code" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.assignWorkers')">
          <WorkerSelect v-model:value="ticketForm.workerIds" :production-unit-id="unitId" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="ticketVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="ticketSaving" @click="submitTicket">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="codeVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.previewCodes')"
      class="w-900px max-w-95vw"
    >
      <NSpin :show="codeLoading">
        <NAlert v-if="codePreview && !codePreview.configured" type="warning">
          {{ $t('page.work_ticket_management.workflow.codeNotConfigured') }}
        </NAlert>
        <NDataTable v-if="codePreview" :columns="codeColumns" :data="codePreview.rows" size="small" />
      </NSpin>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="codeVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="codeLoading" @click="submitCodes">
            {{ $t('page.work_ticket_management.workflow.confirmCodes') }}
          </NButton>
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
      v-model:show="ignoreVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.ignore')"
      class="w-500px max-w-95vw"
    >
      <NInput
        v-model:value="ignoreReason"
        type="textarea"
        :placeholder="$t('page.work_ticket_management.workflow.ignoreReason')"
      />
      <template #footer>
        <NSpace justify="end">
          <NButton @click="ignoreVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitIgnore">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="reopenVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.reopenMonth')"
      class="w-500px max-w-95vw"
    >
      <NInput
        v-model:value="reopenReason"
        type="textarea"
        :placeholder="$t('page.work_ticket_management.workflow.remark')"
      />
      <template #footer>
        <NSpace justify="end">
          <NButton @click="reopenVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="submitReopen">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="statusLogsVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.statusLogs')"
      class="w-900px max-w-95vw"
    >
      <NDataTable :columns="statusLogColumns" :data="statusLogs" :loading="statusLogsLoading" size="small" />
    </NModal>

    <NModal
      v-model:show="ocrVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.ocrCandidates')"
      class="w-760px max-w-95vw"
    >
      <OcrRecognizer :max-size-mb="10" @recognized="onOcrRecognized" />
      <NList v-if="ocrCandidates.length" bordered class="mt-12px">
        <NListItem v-for="(candidate, index) in ocrCandidates" :key="`${candidate.normalized}-${index}`">
          <div class="flex items-center justify-between gap-8px">
            <span>
              {{ candidate.original }} →
              <strong>{{ candidate.normalized }}</strong>
            </span>
            <NTag :type="candidate.match?.ticketId ? 'success' : 'default'" size="small">
              {{
                candidate.match?.ticketId
                  ? $t('page.work_ticket_management.workflow.matched')
                  : $t('page.work_ticket_management.workflow.none')
              }}
            </NTag>
          </div>
        </NListItem>
      </NList>
    </NModal>
  </div>
</template>
