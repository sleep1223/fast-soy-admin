<script setup lang="tsx">
import { onMounted, reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteLaborWorkHour, fetchDeleteLaborWorkHour, fetchGetLaborWorkHourList,
  fetchExportLaborWorkHour, fetchImportLaborWorkHour, fetchPreviewImportLaborWorkHour, fetchLaborWorkHourImportTemplate,
  fetchGetLaborWorkerList
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import LaborWorkHourOperateDrawer from './modules/labor-work-hour-operate-drawer.vue';
import LaborWorkHourSearch from './modules/labor-work-hour-search.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();

type SelectOptionItem = { label: string; value: string | number };

const workerOptions = ref<SelectOptionItem[]>([]);

async function loadWorkers() {
  const options: SelectOptionItem[] = [];
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
  workerOptions.value = options;
}

onMounted(loadWorkers);


const defaultSearchParams: Api.LaborManagementManage.LaborWorkHourSearchParams = {
  current: 1,
  size: 10,
  ticketCode: null,
  orderNo: null,
  workerId: null,
  isAssigned: null,
};

const searchParams: Api.LaborManagementManage.LaborWorkHourSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetLaborWorkHourList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'ticketCode', title: $t('page.labor_management.labor_work_hour.ticketCode'), align: 'center', minWidth: 120 },
    { key: 'workHours', title: $t('page.labor_management.labor_work_hour.workHours'), align: 'center', minWidth: 120 },
    { key: 'orderNo', title: $t('page.labor_management.labor_work_hour.orderNo'), align: 'center', minWidth: 120 },
    { key: 'allocationMonth', title: $t('page.labor_management.labor_work_hour.allocationMonth'), align: 'center', minWidth: 120,
      render: row => row.allocationMonth?.slice(0, 7) ?? '—' },
    { key: 'workerId', title: $t('page.labor_management.labor_work_hour.worker'), align: 'center', minWidth: 120,
      render: row => workerOptions.value.find(option => option.value === row.workerId)?.label ?? '—' },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => (
        <div class="flex-center gap-8px">
          {hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_EDIT') && (
              <NButton type="primary" ghost size="small" onClick={() => edit(row.id)}>
                {$t('common.edit')}
              </NButton>
            )}
          {hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_DELETE') && (
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
  const { error } = await fetchBatchDeleteLaborWorkHour({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteLaborWorkHour({ id });
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
    <LaborWorkHourSearch
      v-model:model="searchParams"
      :worker-options="workerOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.labor_management.labor_work_hour.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportLaborWorkHour"
            :preview-api="fetchPreviewImportLaborWorkHour"
            :export-api="() => fetchExportLaborWorkHour(searchParams)"
            :export-selected-api="ids => fetchExportLaborWorkHour({ ...searchParams, ids })"
            :selected-ids="checkedRowKeys"
            :template-api="fetchLaborWorkHourImportTemplate"
            :can-import="hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_IMPORT')"
            :can-export="hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_EXPORT')"
            @imported="getDataByPage(1)"
          />
          <TableHeaderOperation v-model:columns="columnChecks" :loading="loading" @refresh="getData">
            <NButton
              v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')"
              size="small"
              ghost
              type="primary"
              @click="handleAdd"
            >
              <template #icon><icon-ic-round-plus class="text-icon" /></template>
              {{ $t('common.add') }}
            </NButton>
            <NPopconfirm
              v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_DELETE')"
              @positive-click="handleBatchDelete"
            >
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
      <LaborWorkHourOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :worker-options="workerOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
