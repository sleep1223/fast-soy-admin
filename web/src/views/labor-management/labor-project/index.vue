<script setup lang="tsx">
import { reactive } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteLaborProject, fetchDeleteLaborProject, fetchGetLaborProjectList,
  fetchExportLaborProject, fetchImportLaborProject, fetchPreviewImportLaborProject, fetchLaborProjectImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import LaborProjectOperateDrawer from './modules/labor-project-operate-drawer.vue';
import LaborProjectSearch from './modules/labor-project-search.vue';
import LaborProjectOrders from './modules/labor-project-orders.vue';

const appStore = useAppStore();
const { hasAuth } = useAuth();



const defaultSearchParams: Api.LaborManagementManage.LaborProjectSearchParams = {
  current: 1,
  size: 10,
  partNo: null,
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
    { type: 'expand', expandable: () => true, renderExpand: row => <LaborProjectOrders partNo={row.partNo} /> },
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'partNo', title: $t('page.labor_management.labor_project.partNo'), align: 'center', minWidth: 120 },
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
      <LaborProjectOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
