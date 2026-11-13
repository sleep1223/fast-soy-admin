<script setup lang="tsx">
import { computed, onMounted, ref } from 'vue';
import dayjs from 'dayjs';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NSpace } from 'naive-ui';
import { downloadExcel } from '@/utils/excel';
import {
  fetchAnomalyReport,
  fetchExportReport,
  fetchMonthlyReport,
  fetchOpenWorkMonth,
  fetchProductionUnitOptions,
  fetchTicketStatusReport,
  fetchWorkerDatesReport,
  fetchWorkerHoursReport,
  fetchWorkerOptions
} from '@/service/api';
import { $t } from '@/locales';

defineOptions({ name: 'WorkTicketReports' });

const monthStart = ref(dayjs().format('YYYY-MM'));
const monthEnd = ref(dayjs().format('YYYY-MM'));
const unitId = ref<string | null>(null);
const workerId = ref<string | null>(null);
const basis = ref<Api.WorkTicketManagement.ReportBasis>('ticket_month');
const includeVoid = ref(false);
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const workers = ref<Api.WorkTicketManagement.WorkerOption[]>([]);
const tab = ref<'monthly' | 'workerHours' | 'workerDates' | 'ticketStatus' | 'anomalies'>('monthly');
const loading = ref(false);

const filters = computed<Api.WorkTicketManagement.ReportFilter>(() => ({
  yearMonthStart: monthStart.value,
  yearMonthEnd: monthEnd.value,
  productionUnitId: unitId.value,
  workerId: workerId.value,
  basis: basis.value,
  includeVoid: includeVoid.value
}));

const monthly = ref<Api.WorkTicketManagement.MonthlyReport | null>(null);
const workerHours = ref<Api.WorkTicketManagement.WorkerHoursReport | null>(null);
const workerDates = ref<Api.WorkTicketManagement.WorkerDatesReport | null>(null);
const ticketStatus = ref<Api.WorkTicketManagement.TicketStatusReport | null>(null);
const anomalies = ref<Api.WorkTicketManagement.AnomalyReport | null>(null);

async function load() {
  loading.value = true;
  if (tab.value === 'monthly') {
    const { data } = await fetchMonthlyReport(filters.value);
    monthly.value = data;
  } else if (tab.value === 'workerHours') {
    const { data } = await fetchWorkerHoursReport(filters.value);
    workerHours.value = data;
  } else if (tab.value === 'workerDates') {
    const { data } = await fetchWorkerDatesReport(filters.value);
    workerDates.value = data;
  } else if (tab.value === 'ticketStatus') {
    const { data } = await fetchTicketStatusReport(filters.value);
    ticketStatus.value = data;
  } else {
    if (!unitId.value) {
      anomalies.value = null;
    } else {
      const { data: monthData, error } = await fetchOpenWorkMonth({
        yearMonth: monthStart.value,
        productionUnitId: unitId.value
      });
      if (!error && monthData) {
        const { data } = await fetchAnomalyReport(monthData.id);
        anomalies.value = data;
      }
    }
  }
  loading.value = false;
}

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
}
async function loadWorkers() {
  const { data } = await fetchWorkerOptions(unitId.value, true);
  workers.value = data ?? [];
}
async function exportReport() {
  let workMonthId: string | null = null;
  if (tab.value === 'anomalies' && unitId.value) {
    const { data } = await fetchOpenWorkMonth({ yearMonth: monthStart.value, productionUnitId: unitId.value });
    workMonthId = data?.id ?? null;
  }
  const { data } = await fetchExportReport({ ...filters.value, reportType: tab.value, workMonthId });
  if (data) downloadExcel(data);
}

const monthlyColumns: DataTableColumns<Api.WorkTicketManagement.MonthlyReportRow> = [
  { key: 'yearMonth', title: $t('page.work_ticket_management.workflow.month'), width: 120 },
  { key: 'productionUnitName', title: $t('page.work_ticket_management.workflow.unit'), minWidth: 160 },
  { key: 'ticketCount', title: $t('page.work_ticket_management.workflow.statsTickets'), width: 100 },
  { key: 'assignedCount', title: $t('page.work_ticket_management.workflow.assigned'), width: 100 },
  { key: 'unassignedCount', title: $t('page.work_ticket_management.workflow.unassigned'), width: 100 },
  { key: 'timedCount', title: $t('page.work_ticket_management.workflow.logged'), width: 100 },
  { key: 'noTimeCount', title: $t('page.work_ticket_management.workflow.statsNoTime'), width: 100 },
  { key: 'totalHours', title: $t('page.work_ticket_management.workflow.totalHours'), width: 110 }
];
const workerColumns: DataTableColumns<Api.WorkTicketManagement.WorkerHoursRow> = [
  { key: 'workerName', title: $t('page.work_ticket_management.workflow.worker'), minWidth: 140 },
  { key: 'productionUnitName', title: $t('page.work_ticket_management.workflow.unit'), minWidth: 160 },
  { key: 'ticketCount', title: $t('page.work_ticket_management.workflow.statsTickets'), width: 100 },
  { key: 'hours', title: $t('page.work_ticket_management.workflow.hours'), width: 100 }
];
const dateColumns: DataTableColumns<Api.WorkTicketManagement.WorkerDatesRow> = [
  { key: 'workDate', title: $t('page.work_ticket_management.workflow.workDate'), width: 130 },
  { key: 'workerName', title: $t('page.work_ticket_management.workflow.worker'), minWidth: 140 },
  { key: 'hours', title: $t('page.work_ticket_management.workflow.hours'), width: 100 }
];
const statusColumns: DataTableColumns<Api.WorkTicketManagement.TicketStatusRow> = [
  { key: 'status', title: $t('page.work_ticket_management.workflow.status'), width: 120 },
  { key: 'reconcileStatus', title: $t('page.work_ticket_management.workflow.reconcileStatus'), width: 120 },
  { key: 'count', title: $t('page.work_ticket_management.workflow.statsTickets'), width: 100 }
];
const anomalyColumns: DataTableColumns<Api.WorkTicketManagement.AnomalyRow> = [
  { key: 'category', title: $t('page.work_ticket_management.workflow.anomalies'), minWidth: 180 },
  { key: 'severity', title: $t('page.work_ticket_management.workflow.status'), width: 100 },
  { key: 'count', title: $t('page.work_ticket_management.workflow.statsAnomalies'), width: 100 }
];

onMounted(async () => {
  await loadUnits();
  await loadWorkers();
  await load();
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="card-wrapper">
      <NSpace align="center" wrap>
        <NDatePicker
          v-model:formatted-value="monthStart"
          type="month"
          value-format="yyyy-MM"
          :clearable="false"
          class="w-140px"
        />
        <span>—</span>
        <NDatePicker
          v-model:formatted-value="monthEnd"
          type="month"
          value-format="yyyy-MM"
          :clearable="false"
          class="w-140px"
        />
        <NSelect
          v-model:value="unitId"
          :options="units.map(unit => ({ label: unit.name, value: unit.id }))"
          clearable
          filterable
          class="w-200px"
          @update:value="loadWorkers"
        />
        <NSelect
          v-model:value="workerId"
          :options="workers.map(worker => ({ label: worker.name, value: worker.id }))"
          clearable
          filterable
          class="w-180px"
        />
        <NSelect
          v-model:value="basis"
          :options="[
            { label: $t('page.work_ticket_management.workflow.ticketMonth'), value: 'ticket_month' },
            { label: $t('page.work_ticket_management.workflow.workDateBasis'), value: 'work_date' },
            { label: $t('page.work_ticket_management.workflow.accountingBasis'), value: 'accounting_month' }
          ]"
          class="w-180px"
        />
        <NCheckbox v-model:checked="includeVoid">{{ $t('page.work_ticket_management.workflow.void') }}</NCheckbox>
        <NButton size="small" :loading="loading" @click="load">
          {{ $t('page.work_ticket_management.workflow.search') }}
        </NButton>
        <NButton size="small" @click="exportReport">{{ $t('page.work_ticket_management.workflow.export') }}</NButton>
      </NSpace>
    </NCard>

    <NCard :bordered="false" size="small" class="card-wrapper">
      <NTabs v-model:value="tab" type="line" @update:value="load">
        <NTabPane name="monthly" :tab="$t('page.work_ticket_management.workflow.monthlyReport')">
          <NDataTable :columns="monthlyColumns" :data="monthly?.rows ?? []" :loading="loading" size="small" />
        </NTabPane>
        <NTabPane name="workerHours" :tab="$t('page.work_ticket_management.workflow.workerHours')">
          <NDataTable :columns="workerColumns" :data="workerHours?.rows ?? []" :loading="loading" size="small" />
        </NTabPane>
        <NTabPane name="workerDates" :tab="$t('page.work_ticket_management.workflow.workerDates')">
          <NDataTable :columns="dateColumns" :data="workerDates?.rows ?? []" :loading="loading" size="small" />
        </NTabPane>
        <NTabPane name="ticketStatus" :tab="$t('page.work_ticket_management.workflow.ticketStatus')">
          <NDataTable :columns="statusColumns" :data="ticketStatus?.rows ?? []" :loading="loading" size="small" />
        </NTabPane>
        <NTabPane name="anomalies" :tab="$t('page.work_ticket_management.workflow.anomaliesReport')">
          <NAlert type="info" class="mb-12px">{{ $t('page.work_ticket_management.workflow.selectMonth') }}</NAlert>
          <NDataTable :columns="anomalyColumns" :data="anomalies?.rows ?? []" :loading="loading" size="small" />
        </NTabPane>
      </NTabs>
    </NCard>
  </div>
</template>
