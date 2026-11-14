<script setup lang="tsx">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { onBeforeRouteLeave } from 'vue-router';
import dayjs from 'dayjs';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NInputNumber, NPopconfirm, NSpace } from 'naive-ui';
import {
  downloadExcel
} from '@/utils/excel';
import {
  fetchDeleteTimeEntry,
  fetchExportTimeEntries,
  fetchOpenWorkMonth,
  fetchProductionUnitOptions,
  fetchTimeBatchSave,
  fetchTimeEntries,
  fetchTimeMatrix,
  fetchUpdateTimeEntry,
  fetchWorkMonthSummary
} from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import MonthUnitToolbar from '../shared/month-unit-toolbar.vue';
import WorkerSelect from '../shared/worker-select.vue';

defineOptions({ name: 'WorkTimeEntryPage' });

const { hasAuth } = useAuth();
const month = ref(dayjs().format('YYYY-MM'));
const unitId = ref<string | null>(null);
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const summary = ref<Api.WorkTicketManagement.WorkMonthSummary | null>(null);
const workDate = ref(dayjs().format('YYYY-MM-DD'));
const tab = ref<'matrix' | 'details'>('matrix');
const selectedWorkerIds = ref<string[]>([]);
const matrix = ref<Api.WorkTicketManagement.TimeMatrix | null>(null);
const matrixLoading = ref(false);
const saving = ref(false);
const cellValues = reactive<Record<string, number | null>>({});
const matrixDirty = ref(false);

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
  if (!unitId.value && units.value.length) unitId.value = units.value[0].id;
}
async function ensureMonth() {
  if (!unitId.value) return null;
  const { data, error } = await fetchOpenWorkMonth({ yearMonth: month.value, productionUnitId: unitId.value });
  if (error || !data) return null;
  summary.value = data;
  return data;
}
async function loadMatrix() {
  const monthData = await ensureMonth();
  if (!monthData) return;
  matrixLoading.value = true;
  const { data } = await fetchTimeMatrix({
    workMonthId: monthData.id,
    workerIds: selectedWorkerIds.value.length ? selectedWorkerIds.value : null,
    workDateStart: workDate.value,
    workDateEnd: workDate.value,
    ticketLimit: 100
  });
  matrixLoading.value = false;
  matrix.value = data;
  Object.keys(cellValues).forEach(key => Reflect.deleteProperty(cellValues, key));
  data?.entries.forEach(entry => {
    cellValues[`${entry.ticketId}:${entry.workerId}`] = Number(entry.hours);
  });
  matrixDirty.value = false;
}
async function refreshSummary() {
  if (!summary.value) return;
  const { data } = await fetchWorkMonthSummary(summary.value.id);
  if (data) summary.value = data;
}

function cellKey(ticketId: string, workerId: string) {
  return `${ticketId}:${workerId}`;
}
function cellValue(ticketId: string, workerId: string) {
  return cellValues[cellKey(ticketId, workerId)] ?? null;
}
function setCell(ticketId: string, workerId: string, value: number | null) {
  cellValues[cellKey(ticketId, workerId)] = value !== null && value > 0 ? value : null;
  matrixDirty.value = true;
}
function confirmDiscardMatrix() {
  if (!matrixDirty.value) return true;
  return window.confirm($t('page.work_ticket_management.workflow.unsavedTimeChanges'));
}
onBeforeRouteLeave(() => confirmDiscardMatrix());
function onBeforeUnload(event: BeforeUnloadEvent) {
  if (!matrixDirty.value) return;
  event.preventDefault();
  event.returnValue = '';
}
function existingEntry(ticketId: string, workerId: string) {
  return matrix.value?.entries.find(entry => entry.ticketId === ticketId && entry.workerId === workerId);
}

async function saveMatrix() {
  if (!summary.value || !matrix.value || saving.value) return;
  const entries = [];
  for (const ticket of matrix.value.tickets) {
    for (const worker of matrix.value.workers) {
      const value = cellValue(ticket.id, worker.id);
      const existing = existingEntry(ticket.id, worker.id);
      if (value === null && !existing) continue;
      entries.push({
        ticketId: ticket.id,
        workerId: worker.id,
        workDate: workDate.value,
        hours: value === null ? null : String(value),
        entryId: existing?.id ?? null,
        revision: ticket.revision
      });
    }
  }
  if (!entries.length) {
    window.$message?.info($t('page.work_ticket_management.workflow.noData'));
    return;
  }
  saving.value = true;
  const { error } = await fetchTimeBatchSave({ workMonthId: summary.value.id, entries });
  saving.value = false;
  if (error) {
    window.$message?.error($t('page.work_ticket_management.workflow.saveFailed'));
    return;
  }
  window.$message?.success($t('page.work_ticket_management.workflow.timeSaved'));
  await Promise.all([loadMatrix(), refreshSummary()]);
}

const matrixColumns = computed<DataTableColumns<Api.WorkTicketManagement.TimeMatrixTicket>>(() => {
  const base: DataTableColumns<Api.WorkTicketManagement.TimeMatrixTicket> = [
    { key: 'ticketCode', title: $t('page.work_ticket_management.workflow.ticketCode'), width: 130 },
    { key: 'partNoSnapshot', title: $t('page.work_ticket_management.workflow.partNo'), minWidth: 120 },
    { key: 'orderNoSnapshot', title: $t('page.work_ticket_management.workflow.orderNo'), minWidth: 120 }
  ];
  for (const worker of matrix.value?.workers ?? []) {
    base.push({
      key: `worker_${worker.id}`,
      title: worker.name,
      width: 110,
      render: (ticket: Api.WorkTicketManagement.TimeMatrixTicket) => (
        <NInputNumber
          value={cellValue(ticket.id, worker.id)}
          min={0}
          max={24}
          precision={2}
          showButton={false}
          onUpdateValue={(value: number | null) => setCell(ticket.id, worker.id, value)}
        />
      )
    });
  }
  return base;
});

const details = ref<Api.WorkTicketManagement.TimeEntry[]>([]);
const detailLoading = ref(false);
const detailWorkerId = ref<string | null>(null);
const detailTotal = ref(0);
const detailPage = reactive({ page: 1, size: 20 });
async function loadDetails() {
  const monthData = await ensureMonth();
  if (!monthData) return;
  detailLoading.value = true;
  const { data } = await fetchTimeEntries({
    workMonthId: monthData.id,
    workerId: detailWorkerId.value,
    current: detailPage.page,
    size: detailPage.size
  });
  detailLoading.value = false;
  if (data) {
    details.value = data.records;
    detailTotal.value = data.total;
  }
}

const editVisible = ref(false);
const editSaving = ref(false);
const editForm = reactive({
  id: '',
  revision: 1,
  hours: 0,
  workDate: dayjs().format('YYYY-MM-DD'),
  accountingMonth: null as string | null,
  remark: ''
});
function openEdit(row: Api.WorkTicketManagement.TimeEntry) {
  Object.assign(editForm, {
    id: row.id,
    revision: row.revision,
    hours: Number(row.hours),
    workDate: row.workDate,
    accountingMonth: row.accountingMonth,
    remark: row.remark ?? ''
  });
  editVisible.value = true;
}
async function saveEdit() {
  editSaving.value = true;
  const { error } = await fetchUpdateTimeEntry(editForm.id, {
    revision: editForm.revision,
    hours: String(editForm.hours),
    workDate: editForm.workDate,
    accountingMonth: editForm.accountingMonth,
    remark: editForm.remark || null
  });
  editSaving.value = false;
  if (error) return;
  editVisible.value = false;
  await loadDetails();
}
async function removeEntry(row: Api.WorkTicketManagement.TimeEntry) {
  const { error } = await fetchDeleteTimeEntry(row.id, row.revision);
  if (!error) await loadDetails();
}

const detailColumns: DataTableColumns<Api.WorkTicketManagement.TimeEntry> = [
  { key: 'ticketCode', title: $t('page.work_ticket_management.workflow.ticketCode'), width: 130 },
  { key: 'partNoSnapshot', title: $t('page.work_ticket_management.workflow.partNo'), minWidth: 120 },
  { key: 'workerName', title: $t('page.work_ticket_management.workflow.worker'), width: 120 },
  { key: 'workDate', title: $t('page.work_ticket_management.workflow.workDate'), width: 120 },
  { key: 'effectiveMonth', title: $t('page.work_ticket_management.workflow.accountingMonth'), width: 120 },
  { key: 'hours', title: $t('page.work_ticket_management.workflow.hours'), width: 90 },
  {
    key: 'actions',
    title: $t('page.work_ticket_management.workflow.actions'),
    width: 140,
    render: row => (
      <NSpace size={8}>
        <NButton size="small" onClick={() => openEdit(row)}>
          {$t('common.edit')}
        </NButton>
        <NPopconfirm onPositiveClick={() => removeEntry(row)}>
          {{
            default: () => $t('common.confirmDelete'),
            trigger: () => (
              <NButton size="small" type="error" ghost>
                {$t('common.delete')}
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
];

async function exportEntries() {
  const monthData = await ensureMonth();
  if (!monthData) return;
  const { data } = await fetchExportTimeEntries({ workMonthId: monthData.id, current: 1, size: 1 });
  if (data) downloadExcel(data);
}

watch([month, unitId], () => {
  summary.value = null;
  matrix.value = null;
  if (tab.value === 'matrix') loadMatrix();
  else loadDetails();
});
watch(tab, () => {
  if (tab.value === 'matrix') loadMatrix();
  else loadDetails();
});
watch(workDate, () => {
  if (tab.value === 'matrix') loadMatrix();
});
watch(selectedWorkerIds, () => {
  if (tab.value === 'matrix') loadMatrix();
});
onMounted(async () => {
  window.addEventListener('beforeunload', onBeforeUnload);
  await loadUnits();
  if (unitId.value) await loadMatrix();
});
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload));
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <MonthUnitToolbar
      v-model:month="month"
      v-model:unit-id="unitId"
      :units="units"
      :status="summary?.status"
      :loading="matrixLoading"
    >
      <NButton size="small" @click="tab === 'matrix' ? loadMatrix() : loadDetails()">
        {{ $t('page.work_ticket_management.workflow.refresh') }}
      </NButton>
      <NButton size="small" @click="exportEntries">{{ $t('page.work_ticket_management.workflow.export') }}</NButton>
    </MonthUnitToolbar>

    <NCard :bordered="false" size="small" class="card-wrapper">
      <NTabs v-model:value="tab" type="line">
        <NTabPane name="matrix" :tab="$t('page.work_ticket_management.workflow.timeMatrix')">
          <NSpace class="mb-12px" align="center" wrap>
            <NDatePicker
              v-model:formatted-value="workDate"
              type="date"
              value-format="yyyy-MM-dd"
              :clearable="false"
              class="w-150px"
            />
            <WorkerSelect v-model:value="selectedWorkerIds" :production-unit-id="unitId" class="w-320px" />
            <NButton
              size="small"
              type="primary"
              :loading="saving"
              :disabled="!hasAuth('B_WORK_TICKET_MANAGEMENT_TIME_EDIT')"
              @click="saveMatrix"
            >
              {{ $t('page.work_ticket_management.workflow.batchSave') }}
            </NButton>
            <NText v-if="matrix" depth="3">
              {{ $t('page.work_ticket_management.workflow.totalHours') }}: {{ matrix.totalHours }}
            </NText>
          </NSpace>
          <NAlert v-if="matrix?.truncated" type="warning">
            {{ $t('page.work_ticket_management.workflow.selectedCount', { count: matrix.tickets.length }) }}
          </NAlert>
          <NDataTable
            :columns="matrixColumns"
            :data="matrix?.tickets ?? []"
            :loading="matrixLoading"
            size="small"
            :scroll-x="900"
          />
        </NTabPane>
        <NTabPane name="details" :tab="$t('page.work_ticket_management.workflow.timeDetails')">
          <NSpace class="mb-12px" align="center" wrap>
            <WorkerSelect
              v-model:value="detailWorkerId"
              :production-unit-id="unitId"
              :multiple="false"
              class="w-260px"
            />
            <NButton size="small" @click="loadDetails">{{ $t('page.work_ticket_management.workflow.search') }}</NButton>
          </NSpace>
          <NDataTable
            :columns="detailColumns"
            :data="details"
            :loading="detailLoading"
            size="small"
            remote
            :pagination="{ page: detailPage.page, pageSize: detailPage.size, itemCount: detailTotal, onUpdatePage: (page: number) => { detailPage.page = page; loadDetails(); } }"
          />
        </NTabPane>
      </NTabs>
    </NCard>

    <NModal
      v-model:show="editVisible"
      preset="card"
      :title="$t('page.work_ticket_management.workflow.timeDetails')"
      class="w-520px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.workflow.workDate')">
          <NDatePicker
            v-model:formatted-value="editForm.workDate"
            type="date"
            value-format="yyyy-MM-dd"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.hours')">
          <NInputNumber v-model:value="editForm.hours" :min="0.01" :max="24" :precision="2" class="w-full" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.accountingMonth')">
          <NInput v-model:value="editForm.accountingMonth" placeholder="YYYY-MM" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.workflow.remark')">
          <NInput v-model:value="editForm.remark" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="editVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" :loading="editSaving" @click="saveEdit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>
