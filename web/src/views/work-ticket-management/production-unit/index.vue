<script setup lang="tsx">
import { reactive } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteProductionUnit, fetchDeleteProductionUnit, fetchGetProductionUnitList,
  fetchExportProductionUnit, fetchImportProductionUnit, fetchPreviewImportProductionUnit, fetchProductionUnitImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import ProductionUnitOperateDrawer from './modules/production-unit-operate-drawer.vue';
import ProductionUnitSearch from './modules/production-unit-search.vue';

const appStore = useAppStore();




const defaultSearchParams: Api.WorkTicketManagementManage.ProductionUnitSearchParams = {
  current: 1,
  size: 10,
  code: null,
  name: null,
  enabled: null,
  remark: null,
};

const searchParams: Api.WorkTicketManagementManage.ProductionUnitSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetProductionUnitList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'code', title: $t('page.work_ticket_management.production_unit.code'), align: 'center', minWidth: 120 },
    { key: 'name', title: $t('page.work_ticket_management.production_unit.name'), align: 'center', minWidth: 120 },
    { key: 'enabled', title: $t('page.work_ticket_management.production_unit.enabled'), align: 'center', minWidth: 120 },
    { key: 'remark', title: $t('page.work_ticket_management.production_unit.remark'), align: 'center', minWidth: 120 },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => (
        <div class="flex-center gap-8px">
          <NButton type="primary" ghost size="small" onClick={() => edit(row.id)}>
              {$t('common.edit')}
            </NButton>
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
        </div>
      )
    }
  ]
});

const { drawerVisible, operateType, editingData, handleAdd, handleEdit, checkedRowKeys, onBatchDeleted, onDeleted } =
  useTableOperate(data, 'id', getData);

async function handleBatchDelete() {
  const { error } = await fetchBatchDeleteProductionUnit({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteProductionUnit({ id });
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
    <ProductionUnitSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getDataByPage" />
    <NCard
      :title="$t('page.work_ticket_management.production_unit.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportProductionUnit"
            :preview-api="fetchPreviewImportProductionUnit"
            :export-api="parentFields => fetchExportProductionUnit({ ...searchParams, parentFields })"
            :export-selected-api="
              (ids, parentFields) => fetchExportProductionUnit({ ...searchParams, ids, parentFields })
            "
            :export-parent-fields="[
              { name: 'code', label: $t('page.work_ticket_management.production_unit.code') },
              { name: 'name', label: $t('page.work_ticket_management.production_unit.name') },
              { name: 'enabled', label: $t('page.work_ticket_management.production_unit.enabled') },
              { name: 'remark', label: $t('page.work_ticket_management.production_unit.remark') }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchProductionUnitImportTemplate"
            @imported="getDataByPage(1)"
          />
          <TableHeaderOperation
            v-model:columns="columnChecks"
            :disabled-delete="checkedRowKeys.length === 0"
            :loading="loading"
            @add="handleAdd"
            @delete="handleBatchDelete"
            @refresh="getData"
          />
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
      <ProductionUnitOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
