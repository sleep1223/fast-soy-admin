<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ExcelTransfer from '@/components/advanced/excel-transfer.vue';

import {
  fetchBatchDeleteWorkMonth, fetchDeleteWorkMonth, fetchGetWorkMonthList,
  fetchExportWorkMonth, fetchImportWorkMonth, fetchPreviewImportWorkMonth, fetchWorkMonthImportTemplate
} from '@/service/api';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable, useTableOperate } from '@/hooks/common/table';

import { $t } from '@/locales';
import WorkMonthOperateDrawer from './modules/work-month-operate-drawer.vue';
import WorkMonthSearch from './modules/work-month-search.vue';

const appStore = useAppStore();


type SelectOptionItem = { label: string; value: string | number };

const statusOptions = ref<SelectOptionItem[]>([]);
const productionUnitOptions = ref<SelectOptionItem[]>([]);

// TODO: 在这里加载真实 options 数据源，并传给搜索区和抽屉。


const defaultSearchParams: Api.WorkTicketManagementManage.WorkMonthSearchParams = {
  current: 1,
  size: 10,
  yearMonth: null,
  status: null,
  remark: null,
  revision: null,
  closedAtStart: null,
  closedAtEnd: null,
  closedBy: null,
  reopenedAtStart: null,
  reopenedAtEnd: null,
  reopenCount: null,
  productionUnitId: null,
};

const searchParams: Api.WorkTicketManagementManage.WorkMonthSearchParams = reactive({ ...defaultSearchParams });

const { columns, columnChecks, data, loading, getData, getDataByPage, mobilePagination } = useNaivePaginatedTable({
  api: () => fetchGetWorkMonthList(searchParams),
  transform: response => defaultTransform(response),
  onPaginationParamsChange: params => {
    searchParams.current = params.page;
    searchParams.size = params.pageSize;
  },
  columns: () => [
    { type: 'selection', align: 'center', width: 48 },
    { key: 'index', title: $t('common.index'), width: 64, align: 'center', render: (_, index) => index + 1 },
    { key: 'yearMonth', title: $t('page.work_ticket_management.work_month.yearMonth'), align: 'center', minWidth: 120 },
    { key: 'status', title: $t('page.work_ticket_management.work_month.status'), align: 'center', minWidth: 120 },
    { key: 'remark', title: $t('page.work_ticket_management.work_month.remark'), align: 'center', minWidth: 120 },
    { key: 'revision', title: $t('page.work_ticket_management.work_month.revision'), align: 'center', minWidth: 120 },
    { key: 'closedAt', title: $t('page.work_ticket_management.work_month.closedAt'), align: 'center', minWidth: 120 },
    { key: 'closedBy', title: $t('page.work_ticket_management.work_month.closedBy'), align: 'center', minWidth: 120 },
    { key: 'productionUnitId', title: $t('page.work_ticket_management.work_month.productionUnit'), align: 'center', minWidth: 120 },
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
  const { error } = await fetchBatchDeleteWorkMonth({ ids: checkedRowKeys.value as string[] });
  if (!error) onBatchDeleted();
}

async function handleDelete(id: string) {
  const { error } = await fetchDeleteWorkMonth({ id });
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
    <WorkMonthSearch
      v-model:model="searchParams"
      :status-options="statusOptions"
      :production-unit-options="productionUnitOptions"
      @reset="resetSearchParams"
      @search="getDataByPage"
    />
    <NCard
      :title="$t('page.work_ticket_management.work_month.pageTitle')"
      :bordered="false"
      size="small"
      class="card-wrapper sm:flex-1-hidden"
    >
      <template #header-extra>
        <NSpace align="center" wrap>
          <ExcelTransfer
            :import-api="fetchImportWorkMonth"
            :preview-api="fetchPreviewImportWorkMonth"
            :export-api="parentFields => fetchExportWorkMonth({ ...searchParams, parentFields })"
            :export-selected-api="(ids, parentFields) => fetchExportWorkMonth({ ...searchParams, ids, parentFields })"
            :export-parent-fields="[
              { name: 'year_month', label: $t('page.work_ticket_management.work_month.yearMonth') },
              { name: 'status', label: $t('page.work_ticket_management.work_month.status') },
              { name: 'remark', label: $t('page.work_ticket_management.work_month.remark') },
              { name: 'revision', label: $t('page.work_ticket_management.work_month.revision') },
              { name: 'closed_at', label: $t('page.work_ticket_management.work_month.closedAt') },
              { name: 'closed_by', label: $t('page.work_ticket_management.work_month.closedBy') },
              { name: 'reopened_at', label: $t('page.work_ticket_management.work_month.reopenedAt') },
              { name: 'reopen_count', label: $t('page.work_ticket_management.work_month.reopenCount') },
              { name: 'production_unit_id', label: $t('page.work_ticket_management.work_month.productionUnit') }
            ]"
            :selected-ids="checkedRowKeys"
            :template-api="fetchWorkMonthImportTemplate"
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
      <WorkMonthOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        :status-options="statusOptions"
        :production-unit-options="productionUnitOptions"
        @submitted="getDataByPage"
      />
    </NCard>
  </div>
</template>
