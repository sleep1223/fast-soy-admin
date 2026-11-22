<script setup lang="tsx">
import { onBeforeUnmount, reactive, ref, watch } from 'vue';
import { NButton, NPopconfirm, NSpin, NTag, NTooltip } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteLaborProject, fetchDeleteLaborProject, fetchGetLaborProjectList,
  fetchExportLaborProject, fetchImportLaborProject, fetchPreviewImportLaborProject, fetchLaborProjectImportTemplate, fetchUpdateLaborProject
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import LaborProjectOperateDrawer from './modules/labor-project-operate-drawer.vue';
import LaborProjectSearch from './modules/labor-project-search.vue';
import LaborProjectOrders from './modules/labor-project-orders.vue';
import PaintingStatusSwitch from './modules/painting-status-switch.vue';
import { fetchMatchingOrdersForProjects, projectHasTickets, summarizeOrders } from './modules/matching-orders';

const appStore = useAppStore();
const { hasAuth } = useAuth();
const savingPainting = reactive(new Set<string>());
const expandedRowKeys = ref<(string | number)[]>([]);
let summaryGeneration = 0;

async function setSkipPainting(row: Api.LaborManagementManage.LaborProject, value: boolean, refresh: () => void) {
  if (savingPainting.has(row.id) || !hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_EDIT')) return;
  savingPainting.add(row.id);
  const generation = summaryGeneration;
  try {
    if (value) {
      const hasTickets = await projectHasTickets(row.partNo, () => generation === summaryGeneration);
      if (hasTickets === null || generation !== summaryGeneration) return;
      if (hasTickets) {
        const dialog = window.$dialog;
        if (!dialog) {
          window.$message?.error($t('page.labor_management.labor_project.verifyTicketsFailed'));
          return;
        }
        const confirmed = await new Promise<boolean>(resolve => {
          dialog.warning({
            title: $t('page.labor_management.labor_project.ticketsExistTitle'),
            content: $t('page.labor_management.labor_project.ticketsExistConfirm'),
            positiveText: $t('common.confirm'),
            negativeText: $t('common.cancel'),
            closable: false,
            maskClosable: false,
            closeOnEsc: false,
            onPositiveClick: () => resolve(true),
            onNegativeClick: () => resolve(false)
          });
        });
        if (!confirmed || generation !== summaryGeneration) return;
      }
    }
    const { error } = await fetchUpdateLaborProject({ id: row.id, skipPainting: value });
    if (!error) {
      row.skipPainting = value;
      if (value) expandedRowKeys.value = expandedRowKeys.value.filter(key => key !== row.id);
      refresh();
    }
  } catch {
    window.$message?.error($t('page.labor_management.labor_project.verifyTicketsFailed'));
  } finally {
    savingPainting.delete(row.id);
  }
}
type OrderSummary = ReturnType<typeof summarizeOrders>;
type SummaryState = { loading: boolean; failed: boolean; value: OrderSummary | null };
const summaries = ref<Record<string, SummaryState>>({});

async function loadSummary(row: Api.LaborManagementManage.LaborProject, generation: number) {
  const state = reactive<SummaryState>({ loading: true, failed: false, value: null });
  summaries.value[row.id] = state;
  try {
    const orders = await fetchMatchingOrdersForProjects([row.partNo], () => generation === summaryGeneration && summaries.value[row.id] === state);
    if (orders) state.value = summarizeOrders(orders.get(row.partNo) ?? []);
  } catch {
    if (generation === summaryGeneration && summaries.value[row.id] === state) state.failed = true;
  } finally {
    if (generation === summaryGeneration && summaries.value[row.id] === state) state.loading = false;
  }
}

async function loadPageSummaries(rows: Api.LaborManagementManage.LaborProject[], generation: number) {
  const states = new Map<string, SummaryState>();
  for (const row of rows) {
    const state = reactive<SummaryState>({ loading: true, failed: false, value: null });
    states.set(row.id, state);
    summaries.value[row.id] = state;
  }
  try {
    const grouped = await fetchMatchingOrdersForProjects(rows.map(row => row.partNo), () => generation === summaryGeneration);
    if (!grouped || generation !== summaryGeneration) return;
    for (const row of rows) {
      const state = states.get(row.id);
      if (state && summaries.value[row.id] === state) state.value = summarizeOrders(grouped.get(row.partNo) ?? []);
    }
  } catch {
    if (generation === summaryGeneration) {
      for (const [id, state] of states) if (summaries.value[id] === state) state.failed = true;
    }
  } finally {
    if (generation === summaryGeneration) {
      for (const [id, state] of states) if (summaries.value[id] === state) state.loading = false;
    }
  }
}

function renderSummary(row: Api.LaborManagementManage.LaborProject, key: 'name' | 'processRoute') {
  const state = summaries.value[row.id];
  if (!state || state.loading) return <NSpin size="small" />;
  if (state.failed) return <NButton text type="error" onClick={() => loadSummary(row, summaryGeneration)}>{$t('page.labor_management.labor_project.retryOrders')}</NButton>;
  if (!state.value) return '—';
  const field = state.value[key];
  return <div class="flex-center gap-8px">
    <span>{field.value ?? '—'}</span>
    {field.inconsistent && <NTooltip trigger="hover">{{
      trigger: () => <NTag size="small" type="warning">{$t('page.labor_management.labor_project.inconsistent')}</NTag>,
      default: () => field.variants.map(value => value ?? $t('page.labor_management.labor_project.notProvided')).join(' / ')
    }}</NTooltip>}
  </div>;
}

async function copyProjectNo(value: string) {
  try {
    await navigator.clipboard.writeText(value);
    window.$message?.success($t('page.labor_management.labor_project.copied'));
  } catch {
    window.$message?.error($t('page.labor_management.labor_project.copyFailed'));
  }
}



const defaultSearchParams: Api.LaborManagementManage.LaborProjectSearchParams = {
  current: 1,
  size: 10,
  partNo: null,
  skipPainting: false,
  importedAtStart: null,
  importedAtEnd: null,
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
    { type: 'expand', expandable: row => !row.skipPainting, renderExpand: row => expandedRowKeys.value.includes(row.id) ? <LaborProjectOrders partNo={row.partNo} skipPainting={row.skipPainting} onLoaded={orders => { const state = summaries.value[row.id]; if (state) { state.value = summarizeOrders(orders); state.failed = false; state.loading = false; } }} /> : null },
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    {
      key: 'partNo',
      title: $t('page.labor_management.labor_project.partNo'),
      align: 'center',
      minWidth: 140,
      render: row => (
        <div class="flex-center gap-4px">
          <span class="font-semibold">{row.partNo}</span>
          <NButton
            quaternary
            size="tiny"
            aria-label={$t('page.labor_management.labor_project.copy')}
            onClick={(event: MouseEvent) => {
              event.stopPropagation();
              void copyProjectNo(row.partNo);
            }}
          >
            <icon-ic-round-content-copy class="text-14px" />
          </NButton>
        </div>
      )
    },
    { key: 'importedAt', title: $t('page.labor_management.labor_project.importedAt'), align: 'center', minWidth: 170,
      render: row => row.importedAt == null ? '—' : new Date(row.importedAt).toLocaleDateString() },
    { key: 'workpieceName', title: $t('page.labor_management.labor_project.workpieceName'), align: 'center', minWidth: 160,
      render: row => renderSummary(row, 'name') },
    { key: 'skipPainting', title: $t('page.labor_management.labor_project.skipPainting'), align: 'center', minWidth: 110,
      render: row => <PaintingStatusSwitch value={row.skipPainting} loading={savingPainting.has(row.id)} canEdit={hasAuth('B_LABOR_MANAGEMENT_LABOR_PROJECT_EDIT')} onChange={value => setSkipPainting(row, value, () => { void getData(); })} /> },
    { key: 'processRoutes', title: $t('page.order_management.order.processRoute'), align: 'center', minWidth: 180,
      render: row => renderSummary(row, 'processRoute') },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => (
        <div class="flex-center gap-8px">
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

watch([data, loading], ([rows, isLoading]) => {
  if (isLoading) {
    summaryGeneration += 1;
    expandedRowKeys.value = [];
    summaries.value = {};
    return;
  }
  const generation = ++summaryGeneration;
  const expandableIds = new Set(rows.filter(row => !row.skipPainting).map(row => row.id));
  expandedRowKeys.value = expandedRowKeys.value.filter(key => typeof key === 'string' && expandableIds.has(key));
  summaries.value = {};
  void loadPageSummaries(rows, generation);
}, { immediate: true });
onBeforeUnmount(() => { summaryGeneration += 1; });

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
        v-model:expanded-row-keys="expandedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="1000"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="labor-project-table sm:h-full"
      />
      <LaborProjectOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>

<style scoped>
.labor-project-table :deep(.n-data-table-tr--expanded > .n-data-table-td[colspan]) {
  --detail-background: color-mix(in srgb, var(--n-merged-td-color) 96%, var(--n-td-text-color));
  --n-merged-td-color-hover: var(--detail-background);
  padding: 0;
  background-color: var(--detail-background);
}

.labor-project-table :deep(.n-data-table-expand-trigger--expanded) {
  color: rgb(var(--primary-color));
}

.labor-project-table :deep(.labor-project-detail) {
  margin-block: 12px;
  margin-inline: clamp(12px, 2.5vw, 32px) 12px;
  border-inline-start: 2px solid var(--n-merged-border-color);
  padding-inline-start: 12px;
}

.labor-project-table :deep(.labor-project-detail-heading) {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0 0 8px;
  color: var(--n-th-text-color);
  font-size: 13px;
  font-weight: 600;
}

.labor-project-table :deep(.labor-project-detail-count) {
  color: var(--n-td-text-color);
  font-size: 12px;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
}
</style>
