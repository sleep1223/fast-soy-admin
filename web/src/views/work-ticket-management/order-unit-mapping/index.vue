<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteOrderUnitMapping, fetchDeleteOrderUnitMapping, fetchGetOrderUnitMappingList,
  fetchExportOrderUnitMapping, fetchImportOrderUnitMapping, fetchPreviewImportOrderUnitMapping, fetchOrderUnitMappingImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import OrderUnitMappingOperateDrawer from './modules/order-unit-mapping-operate-drawer.vue';
import OrderUnitMappingSearch from './modules/order-unit-mapping-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const orderOptions = ref<SelectOptionItem[]>([]);
const productionUnitOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.OrderUnitMappingSearchParams = {
  current: 1,
  size: 10,
  remark: null,
  orderId: null,
  productionUnitId: null,
};

const searchParams: Api.WorkTicketManagementManage.OrderUnitMappingSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetOrderUnitMappingList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'remark', title: $t('page.work_ticket_management.order_unit_mapping.remark'), align: 'center', minWidth: 120 },
    { key: 'orderId', title: $t('page.work_ticket_management.order_unit_mapping.order'), align: 'center', minWidth: 120 },
    { key: 'productionUnitId', title: $t('page.work_ticket_management.order_unit_mapping.productionUnit'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteOrderUnitMapping({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteOrderUnitMapping({ id });
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
    <OrderUnitMappingSearch
      v-model:model="searchParams"
      :order-options="orderOptions"
      :production-unit-options="productionUnitOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.order_unit_mapping.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportOrderUnitMapping"
            :preview-api="fetchPreviewImportOrderUnitMapping"
            :export-api="() => fetchExportOrderUnitMapping(searchParams)"
            :export-selected-api="ids => fetchExportOrderUnitMapping({ ...searchParams, ids })"
            :selected-ids="checkedRowKeys"
            :template-api="fetchOrderUnitMappingImportTemplate"
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
      <OrderUnitMappingOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :order-options="orderOptions"
        :production-unit-options="productionUnitOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
