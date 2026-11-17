<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import type { DataTableColumns, UploadCustomRequestOptions } from 'naive-ui';
import { NButton, NTag } from 'naive-ui';
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';
import {
  fetchAssignTicket,
  fetchCreateTicket,
  fetchImportCommit,
  fetchImportPreview,
  fetchImportRows,
  fetchOpenWorkMonth,
  fetchOrderCandidates,
  fetchProductionUnitOptions,
  fetchTickets,
  fetchWorkerOptions
} from '@/service/api';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import MonthUnitToolbar from '../shared/month-unit-toolbar.vue';

defineOptions({ name: 'WorkTicketWorkbench' });

const appStore = useAppStore();
const month = ref(dayjs().format('YYYY-MM'));
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const unitId = ref<string | null>(null);
const workMonthId = ref<string | null>(null);
const loading = ref(false);
const rows = ref<Api.WorkTicketManagement.ImportRow[]>([]);
const total = ref(0);
const keyword = ref('');
const page = reactive({ current: 1, size: 20 });
const selectedRow = ref<Api.WorkTicketManagement.ImportRow | null>(null);
const candidates = ref<Api.WorkTicketManagement.OrderCandidate[]>([]);
const tickets = ref<Api.WorkTicketManagement.Ticket[]>([]);
const workers = ref<Api.WorkTicketManagement.WorkerOption[]>([]);
const onlyUnassigned = ref(false);
let selectionRequest = 0;
let monthRequest = 0;

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
  if (!unitId.value && units.value.length) unitId.value = units.value[0].id;
}

async function openMonth() {
  const currentRequest = ++monthRequest;
  selectionRequest += 1;
  selectedRow.value = null;
  candidates.value = [];
  tickets.value = [];
  workMonthId.value = null;
  rows.value = [];
  total.value = 0;
  if (!unitId.value) {
    loading.value = false;
    return;
  }
  loading.value = true;
  const { data, error } = await fetchOpenWorkMonth({ yearMonth: month.value, productionUnitId: unitId.value });
  if (currentRequest !== monthRequest) return;
  loading.value = false;
  if (error || !data) return;
  workMonthId.value = data.id;
  await Promise.all([loadRows(), loadWorkers()]);
}

async function loadRows() {
  if (!workMonthId.value) return;
  loading.value = true;
  const { data, error } = await fetchImportRows({
    workMonthId: workMonthId.value,
    sourceType: null,
    matchStatus: null,
    keyword: keyword.value.trim() || null,
    current: page.current,
    size: page.size
  });
  loading.value = false;
  if (!error && data) {
    rows.value = data.records;
    total.value = data.total;
    if (selectedRow.value && !rows.value.some(row => row.id === selectedRow.value?.id)) {
      selectedRow.value = null;
      candidates.value = [];
      tickets.value = [];
    }
  }
}

async function loadWorkers() {
  const { data } = await fetchWorkerOptions();
  workers.value = data ?? [];
}

async function selectProject(row: Api.WorkTicketManagement.ImportRow) {
  const currentRequest = ++selectionRequest;
  selectedRow.value = row;
  candidates.value = [];
  tickets.value = [];
  if (!workMonthId.value) return;
  loading.value = true;
  const [ordersResult, ticketsResult] = await Promise.all([
    fetchOrderCandidates({
      workMonthId: workMonthId.value,
      partNo: row.normalizedPartNo || row.rawPartNo,
      limit: 1000,
      includeOtherUnits: true,
      includePartial: false
    }),
    fetchTickets({ workMonthId: workMonthId.value, current: 1, size: 1000 })
  ]);
  if (currentRequest !== selectionRequest) return;
  loading.value = false;
  if (ordersResult.error || ticketsResult.error) {
    window.$message?.error($t('page.work_ticket_management.workflow.loadFailed'));
    return;
  }
  candidates.value = ordersResult.data ?? [];
  const orderIds = new Set(candidates.value.map(order => order.id));
  tickets.value = (ticketsResult.data?.records ?? []).filter(ticket => orderIds.has(ticket.orderId ?? ''));
}

const matchStatusLabels: Record<Api.WorkTicketManagement.MatchStatus, string> = {
  pending: $t('page.work_ticket_management.workflow.pending'),
  matched: $t('page.work_ticket_management.workflow.matched'),
  ambiguous: $t('page.work_ticket_management.workflow.ambiguous'),
  missing: $t('page.work_ticket_management.workflow.missing'),
  unassigned: $t('page.work_ticket_management.workflow.unassigned'),
  other_unit: $t('page.work_ticket_management.workflow.otherUnit'),
  invalid: $t('page.work_ticket_management.workflow.invalid')
};
const mappingStatusLabels: Record<Api.WorkTicketManagement.OrderCandidate['mappingStatus'], string> = {
  confirmed: $t('page.work_ticket_management.workflow.mappingConfirmed'),
  other_unit: $t('page.work_ticket_management.workflow.mappingOther'),
  unconfirmed: $t('page.work_ticket_management.workflow.mappingUnconfirmed')
};

const columns: DataTableColumns<Api.WorkTicketManagement.ImportRow> = [
  { title: $t('page.work_ticket_management.workflow.partNo'), key: 'normalizedPartNo', minWidth: 180 },
  {
    title: $t('page.work_ticket_management.workflow.source'),
    key: 'sourceType',
    width: 100,
    render: row =>
      $t(
        row.sourceType === 'plan'
          ? 'page.work_ticket_management.workflow.plan'
          : 'page.work_ticket_management.workflow.actual'
      )
  },
  {
    title: $t('page.work_ticket_management.workflow.status'),
    key: 'matchStatus',
    width: 120,
    render: row =>
      h(
        NTag,
        {
          type: row.matchStatus === 'matched' ? 'success' : row.matchStatus === 'ambiguous' ? 'warning' : 'default',
          bordered: false,
          size: 'small'
        },
        {
          default: () => matchStatusLabels[row.matchStatus]
        }
      )
  },
  {
    title: $t('page.work_ticket_management.workflow.actions'),
    key: 'actions',
    width: 140,
    render: row =>
      h(
        NButton,
        { size: 'small', type: 'primary', ghost: true, onClick: () => void selectProject(row) },
        { default: () => $t('page.work_ticket_management.workflow.candidateOrders') }
      )
  }
];

// Import one initial list, then supplement it. The backend deduplicates both
// sources on normalized project number, so a supplement never adds an existing number.
const importVisible = ref(false);
const importSource = ref<Api.WorkTicketManagement.ImportSourceType>('plan');
const importFile = ref<File | null>(null);
const importPreview = ref<Api.WorkTicketManagement.ImportPreview | null>(null);
const importBusy = ref(false);
function openImport(source: Api.WorkTicketManagement.ImportSourceType) {
  importSource.value = source;
  importFile.value = null;
  importPreview.value = null;
  importVisible.value = true;
}
async function previewFile(options: UploadCustomRequestOptions) {
  if (!options.file.file || !workMonthId.value) return options.onError();
  importBusy.value = true;
  const { data, error } = await fetchImportPreview(options.file.file, workMonthId.value, importSource.value);
  importBusy.value = false;
  if (error || !data) return options.onError();
  importFile.value = options.file.file;
  importPreview.value = data;
  options.onFinish();
}
async function commitImport() {
  if (!importFile.value || !workMonthId.value) return;
  importBusy.value = true;
  const { data, error } = await fetchImportCommit(importFile.value, workMonthId.value, importSource.value);
  importBusy.value = false;
  if (error || !data) return;
  importVisible.value = false;
  window.$message?.success(
    $t('page.work_ticket_management.workflow.importCompleted', {
      count: data.rowCount,
      duplicates: data.duplicateRows
    })
  );
  page.current = 1;
  await loadRows();
}

const ticketVisible = ref(false);
const ticketSaving = ref(false);
const selectedOrder = ref<Api.WorkTicketManagement.OrderCandidate | null>(null);
const ticketForm = reactive({
  code: '',
  codeSource: 'manual'
});
function openTicket(order: Api.WorkTicketManagement.OrderCandidate) {
  selectedOrder.value = order;
  Object.assign(ticketForm, {
    code: '',
    codeSource: 'manual'
  });
  ticketVisible.value = true;
}
async function copyOrderNo(orderNo: string) {
  try {
    await navigator.clipboard.writeText(orderNo);
    window.$message?.success($t('page.work_ticket_management.workflow.orderCodeCopied'));
  } catch {
    window.$message?.error($t('page.work_ticket_management.workflow.copyFailed'));
  }
}
function onOcrRecognized(result: Api.Ocr.Result) {
  ticketForm.code = result.text.trim();
  ticketForm.codeSource = 'ocr';
}
async function saveTicket() {
  if (!workMonthId.value || !selectedRow.value || !selectedOrder.value) return;
  if (!ticketForm.code.trim()) {
    window.$message?.warning($t('page.work_ticket_management.workflow.ticketCodeRequired'));
    return;
  }
  ticketSaving.value = true;
  const { data: ticket, error } = await fetchCreateTicket({
    workMonthId: workMonthId.value,
    orderId: selectedOrder.value.id,
    sourceImportRowId: selectedRow.value.id,
    partNoSnapshot: selectedOrder.value.partNo,
    nameSnapshot: selectedOrder.value.name,
    ticketCode: ticketForm.code.trim() || null,
    codeSource: ticketForm.codeSource,
    allowAddMapping: true
  });
  if (error || !ticket) {
    ticketSaving.value = false;
    return;
  }
  ticketSaving.value = false;
  ticketVisible.value = false;
  await selectProject(selectedRow.value);
  window.$message?.success($t('page.work_ticket_management.workflow.saveSuccess'));
}

const assignmentVisible = ref(false);
const assignmentSaving = ref(false);
const assigningTicket = ref<Api.WorkTicketManagement.Ticket | null>(null);
const assignmentWorkerIds = ref<string[]>([]);
function openAssignment(ticket: Api.WorkTicketManagement.Ticket) {
  assigningTicket.value = ticket;
  assignmentWorkerIds.value = [];
  assignmentVisible.value = true;
}
async function saveAssignment() {
  if (!assigningTicket.value || !assignmentWorkerIds.value.length) return;
  assignmentSaving.value = true;
  const { error } = await fetchAssignTicket(
    assigningTicket.value.id,
    assigningTicket.value.revision,
    assignmentWorkerIds.value
  );
  assignmentSaving.value = false;
  if (error) return;
  assignmentVisible.value = false;
  if (selectedRow.value) await selectProject(selectedRow.value);
  window.$message?.success($t('page.work_ticket_management.workflow.saveSuccess'));
}

const visibleTickets = computed(() =>
  onlyUnassigned.value ? tickets.value.filter(ticket => ticket.assignmentCount === 0) : tickets.value
);
function ticketsForOrder(orderId: string) {
  return visibleTickets.value.filter(ticket => ticket.orderId === orderId);
}
const ticketColumns: DataTableColumns<Api.WorkTicketManagement.Ticket> = [
  {
    title: $t('page.work_ticket_management.workflow.ticketCode'),
    key: 'ticketCode',
    render: ticket => ticket.ticketCode || '—'
  },
  {
    title: $t('page.work_ticket_management.workflow.assignment'),
    key: 'workerNames',
    render: ticket => ticket.workerNames.join('、') || $t('page.work_ticket_management.workflow.unassigned')
  },
  {
    title: $t('page.work_ticket_management.workflow.totalHours'),
    key: 'totalHours',
    render: ticket => `${ticket.totalHours} ${$t('page.work_ticket_management.workflow.hours')}`
  },
  {
    title: $t('page.work_ticket_management.workflow.actions'),
    key: 'actions',
    width: 140,
    render: ticket =>
      h(
        NButton,
        {
          size: 'small',
          type: 'primary',
          ghost: true,
          disabled: ticket.status !== 'active',
          onClick: () => openAssignment(ticket)
        },
        { default: () => $t('page.work_ticket_management.workflow.assignWorkers') }
      )
  }
];
const previewColumns: DataTableColumns<Api.WorkTicketManagement.ImportPreviewRow> = [
  { title: $t('page.work_ticket_management.workflow.partNo'), key: 'rawPartNo' },
  {
    title: $t('page.work_ticket_management.workflow.orderNo'),
    key: 'orderNo',
    render: row =>
      row.orderNo ||
      (row.duplicateOfRowId
        ? $t('page.work_ticket_management.workflow.duplicate')
        : $t('page.work_ticket_management.workflow.unmatched'))
  },
  { title: $t('page.work_ticket_management.workflow.remark'), key: 'note' }
];

onMounted(async () => {
  await loadUnits();
});
watch([month, unitId], () => void openMonth());
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <MonthUnitToolbar v-model:month="month" v-model:unit-id="unitId" :units="units" :loading="loading">
      <NButton size="small" type="primary" :disabled="!workMonthId" @click="openImport('plan')">
        {{ $t('page.work_ticket_management.workflow.importPlan') }}
      </NButton>
      <NButton size="small" :disabled="!workMonthId" @click="openImport('actual')">
        {{ $t('page.work_ticket_management.workflow.importActual') }}
      </NButton>
    </MonthUnitToolbar>

    <NGrid cols="1 900:2" :x-gap="16" :y-gap="16" responsive="screen" class="sm:flex-1-hidden">
      <NGi>
        <NCard
          :title="$t('page.work_ticket_management.workflow.importRows')"
          :bordered="false"
          size="small"
          class="card-wrapper sm:flex-1-hidden"
        >
          <template #header-extra>
            <NSpace align="center" wrap>
              <NInput
                v-model:value="keyword"
                clearable
                :placeholder="$t('page.work_ticket_management.workflow.searchProjectNumbers')"
                class="w-180px"
                @keyup.enter="loadRows"
              />
              <NButton size="small" @click="loadRows">{{ $t('page.work_ticket_management.workflow.search') }}</NButton>
            </NSpace>
          </template>
          <NDataTable
            :columns="columns"
            :data="rows"
            :loading="loading"
            :flex-height="!appStore.isMobile"
            :row-key="row => row.id"
            :row-props="row => ({ onDblclick: () => selectProject(row) })"
            :scroll-x="600"
            :pagination="{
              page: page.current,
              pageSize: page.size,
              itemCount: total,
              onUpdatePage: (value: number) => {
                page.current = value;
                loadRows();
              },
              onUpdatePageSize: (value: number) => {
                page.size = value;
                page.current = 1;
                loadRows();
              }
            }"
            size="small"
            class="sm:h-full"
          />
          <div class="mt-8px text-12px text-gray">
            {{ $t('page.work_ticket_management.workflow.importProjectHint') }}
          </div>
        </NCard>
      </NGi>

      <NGi>
        <NCard
          :title="
            selectedRow
              ? `${$t('page.work_ticket_management.workflow.partNo')}：${selectedRow.normalizedPartNo}`
              : $t('page.work_ticket_management.workflow.candidateOrders')
          "
          :bordered="false"
          size="small"
          class="card-wrapper sm:flex-1-hidden"
        >
          <NEmpty v-if="!selectedRow" :description="$t('page.work_ticket_management.workflow.selectRowHint')" />
          <template v-else>
            <div class="mb-12px flex flex-wrap items-center justify-between gap-8px">
              <div class="text-13px text-gray">
                {{ $t('page.work_ticket_management.workflow.orderCount', { count: candidates.length }) }}
              </div>
              <NSwitch v-model:value="onlyUnassigned">
                <template #checked>{{ $t('page.work_ticket_management.workflow.onlyUnassigned') }}</template>
                <template #unchecked>{{ $t('page.work_ticket_management.workflow.showAllTickets') }}</template>
              </NSwitch>
            </div>
            <div class="max-h-full overflow-y-auto pr-4px">
              <NEmpty
                v-if="!candidates.length"
                :description="$t('page.work_ticket_management.workflow.noCandidates')"
              />
              <NCard v-for="order in candidates" :key="order.id" :bordered="true" size="small" class="mb-12px">
                <template #header>
                  <div class="flex flex-wrap items-center gap-8px">
                    <span class="text-15px font-600">{{ order.orderNo }}</span>
                    <NTag
                      size="small"
                      :bordered="false"
                      :type="order.mappingStatus === 'confirmed' ? 'success' : 'warning'"
                    >
                      {{ mappingStatusLabels[order.mappingStatus] }}
                    </NTag>
                  </div>
                </template>
                <div class="grid grid-cols-1 gap-x-20px gap-y-6px text-13px sm:grid-cols-2">
                  <div>
                    <span class="text-gray">{{ $t('page.work_ticket_management.workflow.partNo') }}：</span>
                    {{ order.partNo }}
                  </div>
                  <div>
                    <span class="text-gray">{{ $t('page.work_ticket_management.workflow.name') }}：</span>
                    {{ order.name }}
                  </div>
                  <div>
                    <span class="text-gray">{{ $t('page.work_ticket_management.workflow.quantity') }}：</span>
                    {{ order.quantity ?? '—' }}
                  </div>
                  <div>
                    <span class="text-gray">{{ $t('page.work_ticket_management.workflow.receivedQuantity') }}：</span>
                    {{ order.receivedQuantity ?? '—' }}
                  </div>
                </div>
                <div class="mt-12px flex flex-wrap justify-end gap-8px">
                  <NButton size="small" secondary @click="copyOrderNo(order.orderNo)">
                    {{ $t('page.work_ticket_management.workflow.copyOrderNo') }}
                  </NButton>
                  <NButton size="small" type="primary" @click="openTicket(order)">
                    {{ $t('page.work_ticket_management.workflow.enterTicketCode') }}
                  </NButton>
                </div>
                <NDivider class="my-12px" />
                <div class="mb-8px text-13px font-600">{{ $t('page.work_ticket_management.workflow.ticket') }}</div>
                <NEmpty
                  v-if="!ticketsForOrder(order.id).length"
                  :description="
                    $t(
                      onlyUnassigned
                        ? 'page.work_ticket_management.workflow.noUnassignedTicket'
                        : 'page.work_ticket_management.workflow.noTicket'
                    )
                  "
                  size="small"
                />
                <NDataTable
                  v-else
                  :columns="ticketColumns"
                  :data="ticketsForOrder(order.id)"
                  :row-key="ticket => ticket.id"
                  size="small"
                  :scroll-x="700"
                />
              </NCard>
            </div>
          </template>
        </NCard>
      </NGi>
    </NGrid>

    <NModal
      v-model:show="importVisible"
      preset="card"
      :title="
        $t(
          importSource === 'plan'
            ? 'page.work_ticket_management.workflow.importPlan'
            : 'page.work_ticket_management.workflow.importActual'
        )
      "
      class="w-760px max-w-95vw"
    >
      <NSpace vertical>
        <NAlert type="info" :show-icon="false">
          {{ $t('page.work_ticket_management.workflow.importProjectHint') }}
        </NAlert>
        <NUpload accept=".xlsx" :max="1" :custom-request="previewFile" :show-file-list="true">
          <NButton :loading="importBusy">{{ $t('page.work_ticket_management.workflow.chooseExcel') }}</NButton>
        </NUpload>
        <template v-if="importPreview">
          <NAlert type="info" :show-icon="false">
            {{
              $t('page.work_ticket_management.workflow.importPreviewSummary', {
                total: importPreview.totalRows,
                added: importPreview.totalRows - importPreview.duplicateRows - importPreview.invalidRows,
                duplicates: importPreview.duplicateRows,
                invalid: importPreview.invalidRows
              })
            }}
          </NAlert>
          <NDataTable
            :columns="previewColumns"
            :data="importPreview.rows"
            :max-height="320"
            :scroll-x="600"
            size="small"
          />
          <div class="flex justify-end">
            <NButton type="primary" :loading="importBusy" @click="commitImport">
              {{ $t('page.work_ticket_management.workflow.importConfirm') }}
            </NButton>
          </div>
        </template>
      </NSpace>
    </NModal>

    <NModal
      v-model:show="ticketVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.enterTicketCode')"
      class="w-560px max-w-95vw"
    >
      <NSpace vertical :size="16">
        <NAlert type="info" :show-icon="false">
          {{ $t('page.work_ticket_management.workflow.externalTicketCodeHint') }}
        </NAlert>
        <NForm label-placement="top">
          <NFormItem :label="$t('page.work_ticket_management.workflow.orderNo')">
            <NSpace class="w-full" align="center" :wrap="false">
              <NInput :value="selectedOrder?.orderNo" readonly class="flex-1" />
              <NButton secondary @click="selectedOrder && copyOrderNo(selectedOrder.orderNo)">
                {{ $t('page.work_ticket_management.workflow.copyOrderNo') }}
              </NButton>
            </NSpace>
          </NFormItem>
          <NFormItem :label="$t('page.work_ticket_management.workflow.ticketCode')" required>
            <NInput
              v-model:value="ticketForm.code"
              :placeholder="$t('page.work_ticket_management.workflow.pasteTicketCode')"
            />
          </NFormItem>
          <NFormItem :label="$t('page.work_ticket_management.workflow.ocr')">
            <OcrRecognizer @recognized="onOcrRecognized" />
          </NFormItem>
        </NForm>
      </NSpace>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="ticketVisible = false">{{ $t('page.work_ticket_management.workflow.cancel') }}</NButton>
          <NButton type="primary" :loading="ticketSaving" @click="saveTicket">
            {{ $t('page.work_ticket_management.workflow.save') }}
          </NButton>
        </NSpace>
      </template>
    </NModal>

    <NModal
      v-model:show="assignmentVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.assignWorkers')"
      class="w-560px max-w-95vw"
    >
      <NSpace vertical :size="16">
        <NAlert type="info" :show-icon="false">
          {{ $t('page.work_ticket_management.workflow.assignHint') }}
        </NAlert>
        <NForm label-placement="top">
          <NFormItem :label="$t('page.work_ticket_management.workflow.ticketCode')">
            <NInput :value="assigningTicket?.ticketCode || '—'" readonly />
          </NFormItem>
          <NFormItem :label="$t('page.work_ticket_management.workflow.worker')" required>
            <NSelect
              v-model:value="assignmentWorkerIds"
              multiple
              filterable
              clearable
              max-tag-count="responsive"
              :options="
                workers.filter(worker => worker.enabled).map(worker => ({ label: worker.name, value: worker.id }))
              "
              :placeholder="$t('page.work_ticket_management.workflow.noWorkers')"
            />
          </NFormItem>
        </NForm>
      </NSpace>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="assignmentVisible = false">{{ $t('page.work_ticket_management.workflow.cancel') }}</NButton>
          <NButton
            type="primary"
            :disabled="!assignmentWorkerIds.length"
            :loading="assignmentSaving"
            @click="saveAssignment"
          >
            {{ $t('page.work_ticket_management.workflow.assignWorkers') }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>
