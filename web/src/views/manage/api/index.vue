<script setup lang="tsx">
import { NButton, NPopconfirm, NTag } from 'naive-ui';
import { fetchBatchDeleteApi, fetchDeleteApi, fetchGetApiList, fetchRefreshAPI } from '@/service/api';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { apiMethodRecord, enableStatusRecord } from '@/constants/business';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import ApiOperateDrawer from './modules/api-operate-drawer.vue';
import ApiSearch from './modules/api-search.vue';

const appStore = useAppStore();

const { columns, columnChecks, data, getData, loading, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetApiList,
  showTotal: true,
  apiParams: {
    current: 1,
    size: 10,
    // if you want to use the searchParams in Form, you need to define the following properties, and the value is null
    // the value can not be undefined, otherwise the property in Form will not be reactive
    status: null,
    path: null,
    method: null,
    summary: null,
    tags: null
  },
  columns: () => [
    {
      type: 'selection',
      align: 'center',
      width: 48
    },
    {
      key: 'index',
      title: $t('common.index'),
      align: 'center',
      width: 64
    },
    {
      key: 'path',
      title: $t('page.manage.api.path'),
      align: 'center',
      minWidth: 50
    },
    {
      key: 'method',
      title: $t('page.manage.api.method'),
      align: 'center',
      width: 100,
      render: row => {
        if (row.method === null) {
          return null;
        }

        const tagMap: Record<Api.SystemManage.methods, NaiveUI.ThemeColor> = {
          get: 'primary',
          post: 'warning',
          put: 'info',
          patch: 'success',
          delete: 'error'
        };

        const label = $t(apiMethodRecord[row.method]);

        return <NTag type={tagMap[row.method]}>{label}</NTag>;
      }
    },
    {
      key: 'summary',
      title: $t('page.manage.api.summary'),
      align: 'center',
      minWidth: 50
    },
    {
      key: 'tags',
      title: $t('page.manage.api.tags'),
      align: 'center',
      width: 300,
      render: row => {
        if (row.tags === null) {
          return null;
        }
        return row.tags.split('|').map((tag, index) => (
          <span>
            <NTag type="error">{tag}</NTag>
            {index < row.tags.split('|').length - 1 && <span style="margin-right: 4px;"> -&gt;</span>}
          </span>
        ));
      }
    },
    {
      key: 'status',
      title: $t('page.manage.api.status'),
      align: 'center',
      width: 100,
      render: row => {
        if (row.status === null) {
          return null;
        }
        const tagMap: Record<Api.Common.EnableStatus, NaiveUI.ThemeColor> = {
          1: 'success',
          2: 'warning'
        };
        const label = $t(enableStatusRecord[row.status]);
        return <NTag type={tagMap[row.status]}>{label}</NTag>;
      }
    },
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

const {
  drawerVisible,
  operateType,
  editingData,
  handleAdd,
  handleEdit,
  checkedRowKeys,
  onBatchDeleted,
  onDeleted
  // closeDrawer
} = useTableOperate(data, getData);
const { hasAuth } = useAuth();

async function handleRefreshAPI() {
  // request
  await fetchRefreshAPI();
  await getData();
}

async function handleBatchDelete() {
  // request
  const { error } = await fetchBatchDeleteApi({ ids: checkedRowKeys.value });
  if (!error) {
    onBatchDeleted();
  }
}

async function handleDelete(id: number) {
  // request
  const { error } = await fetchDeleteApi({ id });
  if (!error) {
    onDeleted();
  }
}

function edit(id: number) {
  handleEdit(id);
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <ApiSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getData" />
    <NCard :title="$t('page.manage.api.title')" :bordered="false" size="small" class="sm:flex-1-hidden card-wrapper">
      <template #header-extra>
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading"
          @add="handleAdd"
          @delete="handleBatchDelete"
          @refresh="getData"
        >
          <template #default>
            <NButton v-if="hasAuth('B_refreshAPI')" size="small" ghost type="primary" @click="handleRefreshAPI">
              <template #icon>
                <icon-ic-round-plus class="text-icon" />
              </template>
              {{ $t('common.refreshAPI') }}
            </NButton>
            <span></span>
          </template>
        </TableHeaderOperation>
      </template>
      <NDataTable
        v-model:checked-row-keys="checkedRowKeys"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="962"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />
      <ApiOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getData"
      />
    </NCard>
  </div>
</template>

<style scoped></style>
