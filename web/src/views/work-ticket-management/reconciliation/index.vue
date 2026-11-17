<script setup lang="tsx">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NSpace, NTag } from 'naive-ui';
import {
  downloadExcel
} from '@/utils/excel';
import {
  fetchCloseWorkMonth,
  fetchExportWorkMonthWorkbook,
  fetchIgnoreImportRow,
  fetchOpenWorkMonth,
  fetchProductionUnitOptions,
  fetchReconciliationItems,
  fetchReconciliationSummary,
  fetchReopenWorkMonth,
  fetchTicket,
  fetchReconcileTicket,
  fetchVerifyWorkMonth,
  fetchWorkMonthSummary
} from '@/service/api';
import { $t } from '@/locales';
import MonthUnitToolbar from '../shared/month-unit-toolbar.vue';

defineOptions({ name: 'WorkTicketReconciliation' });

const month = ref(dayjs().format('YYYY-MM'));
const unitId = ref<string | null>(null);
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const summary = ref<Api.WorkTicketManagement.ReconcileSummary | null>(null);
const monthSummary = ref<Api.WorkTicketManagement.WorkMonthSummary | null>(null);
const activeCategory = ref<Api.WorkTicketManagement.ReconcileCategory>('ambiguous');
const items = ref<Api.WorkTicketManagement.ReconcileItem[]>([]);
const loading = ref(false);
const total = ref(0);
const page = reactive({ current: 1, size: 20 });

const categoryLabels: Array<{ key: Api.WorkTicketManagement.ReconcileCategory; label: string }> = [
  { key: 'ambiguous', label: $t('page.work_ticket_management.workflow.categoryAmbiguous') },
  { key: 'unassigned', label: $t('page.work_ticket_management.workflow.categoryUnassigned') },
  { key: 'no_time', label: $t('page.work_ticket_management.workflow.categoryNoTime') },
  { key: 'ticket_without_order', label: $t('page.work_ticket_management.workflow.categoryTicketNoOrder') },
  { key: 'actual_without_ticket', label: $t('page.work_ticket_management.workflow.categoryActualNoTicket') },
  { key: 'plan_missing_actual', label: $t('page.work_ticket_management.workflow.categoryPlanMissing') },
  { key: 'actual_missing_plan', label: $t('page.work_ticket_management.workflow.categoryActualMissing') },
  { key: 'duplicate_code', label: $t('page.work_ticket_management.workflow.categoryDuplicateCode') },
  { key: 'cross_month_duplicate', label: $t('page.work_ticket_management.workflow.categoryCrossMonth') }
];

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
  if (!unitId.value && units.value.length) unitId.value = units.value[0].id;
}
async function ensureMonth() {
  if (!unitId.value) return null;
  const { data, error } = await fetchOpenWorkMonth({ yearMonth: month.value, productionUnitId: unitId.value });
  if (error || !data) return null;
  monthSummary.value = data;
  return data;
}
async function loadSummary() {
  const monthData = await ensureMonth();
  if (!monthData) return;
  const [recon, monthDataSummary] = await Promise.all([fetchReconciliationSummary(monthData.id), fetchWorkMonthSummary(monthData.id)]);
  if (recon.data) summary.value = recon.data;
  if (monthDataSummary.data) monthSummary.value = monthDataSummary.data;
}
async function loadItems() {
  const monthData = await ensureMonth();
  if (!monthData) return;
  loading.value = true;
  const { data } = await fetchReconciliationItems(monthData.id, {
    category: activeCategory.value,
    current: page.current,
    size: page.size
  });
  loading.value = false;
  if (data) {
    items.value = data.records;
    total.value = data.total;
  }
}
async function refresh() {
  await Promise.all([loadSummary(), loadItems()]);
}
const counts = computed(() => summary.value?.counts ?? ({} as Record<string, number>));

const ignoreVisible = ref(false);
const ignoreReason = ref('');
const ignoring = ref<Api.WorkTicketManagement.ReconcileItem | null>(null);
function openIgnore(item: Api.WorkTicketManagement.ReconcileItem) {
  ignoring.value = item;
  ignoreReason.value = '';
  ignoreVisible.value = true;
}
async function submitIgnore() {
  if (!ignoring.value || !ignoreReason.value.trim()) return;
  const item = ignoring.value;
  if (item.entityType === 'import_row' && item.entityId) {
    const { error } = await fetchIgnoreImportRow(item.entityId, ignoreReason.value.trim());
    if (error) return;
  } else if (item.entityType === 'work_ticket' && item.entityId) {
    const { data } = await fetchTicket(item.entityId);
    if (!data) return;
    const { error } = await fetchReconcileTicket(item.entityId, data.revision, 'ignored', ignoreReason.value.trim());
    if (error) return;
  }
  ignoreVisible.value = false;
  await refresh();
}

const columns: DataTableColumns<Api.WorkTicketManagement.ReconcileItem> = [
  {
    key: 'severity',
    title: $t('page.work_ticket_management.workflow.status'),
    width: 90,
    render: row => <NTag size="small" type={row.severity === 'blocking' ? 'error' : 'warning'}>{row.severity === 'blocking' ? $t('page.work_ticket_management.workflow.blocking') : $t('page.work_ticket_management.workflow.warning')}</NTag>
  },
  { key: 'title', title: $t('page.work_ticket_management.workflow.name'), minWidth: 180 },
  { key: 'detail', title: $t('page.work_ticket_management.workflow.remark'), minWidth: 260 },
  { key: 'key', title: 'Key', minWidth: 180 },
  {
    key: 'actions',
    title: $t('page.work_ticket_management.workflow.actions'),
    width: 130,
    render: row =>
      row.actions.includes('ignore') ? (
        <NButton size="small" onClick={() => openIgnore(row)}>
          {$t('page.work_ticket_management.workflow.ignore')}
        </NButton>
      ) : (
        <span>—</span>
      )
  }
];

async function verifyMonth() {
  if (!monthSummary.value) return;
  const { data } = await fetchVerifyWorkMonth(monthSummary.value.id, { revision: monthSummary.value.revision });
  if (data) monthSummary.value = data;
  await refresh();
}
async function closeMonth() {
  if (!monthSummary.value) return;
  const { data } = await fetchCloseWorkMonth(monthSummary.value.id, { revision: monthSummary.value.revision, confirmWarnings: true });
  if (data) monthSummary.value = data;
  await refresh();
}
const reopenVisible = ref(false);
const reopenReason = ref('');
async function submitReopen() {
  if (!monthSummary.value || !reopenReason.value.trim()) return;
  const { data, error } = await fetchReopenWorkMonth(monthSummary.value.id, { revision: monthSummary.value.revision, reason: reopenReason.value.trim() });
  if (error || !data) return;
  monthSummary.value = data;
  reopenVisible.value = false;
  reopenReason.value = '';
  await refresh();
}
async function exportMonth() {
  if (!monthSummary.value) return;
  const { data } = await fetchExportWorkMonthWorkbook(monthSummary.value.id);
  if (data) downloadExcel(data);
}

watch([month, unitId], () => {
  summary.value = null;
  monthSummary.value = null;
  page.current = 1;
  refresh();
});
watch(activeCategory, () => {
  page.current = 1;
  loadItems();
});
onMounted(loadUnits);
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <MonthUnitToolbar v-model:month="month" v-model:unit-id="unitId" :units="units" :status="monthSummary?.status">
      <NButton size="small" @click="refresh">{{ $t('page.work_ticket_management.workflow.refresh') }}</NButton>
      <NButton size="small" @click="exportMonth">{{ $t('page.work_ticket_management.workflow.export') }}</NButton>
      <NButton size="small" :disabled="monthSummary?.status !== 'in_progress'" @click="verifyMonth">
        {{ $t('page.work_ticket_management.workflow.verifyMonth') }}
      </NButton>
      <NButton size="small" :disabled="monthSummary?.status !== 'verified'" @click="closeMonth">
        {{ $t('page.work_ticket_management.workflow.closeMonth') }}
      </NButton>
      <NButton
        size="small"
        :disabled="!monthSummary || !['verified', 'closed'].includes(monthSummary.status)"
        @click="reopenVisible = true"
      >
        {{ $t('page.work_ticket_management.workflow.reopenMonth') }}
      </NButton>
    </MonthUnitToolbar>

    <NAlert v-if="summary && !summary.hasActualBatch" type="warning">
      {{ $t('page.work_ticket_management.workflow.actualNotReconciled') }}
    </NAlert>

    <NGrid v-if="summary" cols="1 s:2 m:3 l:5" responsive="screen" :x-gap="12" :y-gap="12">
      <NGi><NStatistic :label="$t('page.work_ticket_management.workflow.blocking')" :value="summary.blocking" /></NGi>
      <NGi><NStatistic :label="$t('page.work_ticket_management.workflow.warning')" :value="summary.warnings" /></NGi>
      <NGi>
        <NStatistic
          :label="$t('page.work_ticket_management.workflow.categoryAmbiguous')"
          :value="counts.ambiguous ?? 0"
        />
      </NGi>
      <NGi>
        <NStatistic
          :label="$t('page.work_ticket_management.workflow.categoryUnassigned')"
          :value="counts.unassigned ?? 0"
        />
      </NGi>
      <NGi>
        <NStatistic :label="$t('page.work_ticket_management.workflow.categoryNoTime')" :value="counts.no_time ?? 0" />
      </NGi>
    </NGrid>

    <NCard :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <NTabs v-model:value="activeCategory" type="line">
        <NTabPane
          v-for="category in categoryLabels"
          :key="category.key"
          :name="category.key"
          :tab="`${category.label} (${counts[category.key] ?? 0})`"
        />
      </NTabs>
      <NDataTable
        :columns="columns"
        :data="items"
        :loading="loading"
        size="small"
        remote
        :scroll-x="900"
        :pagination="{ page: page.current, pageSize: page.size, itemCount: total, onUpdatePage: (value: number) => { page.current = value; loadItems(); } }"
      />
    </NCard>

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
  </div>
</template>
