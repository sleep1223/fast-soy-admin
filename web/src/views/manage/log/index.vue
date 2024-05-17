<script setup lang="tsx">
import { NButton, NTag } from 'naive-ui';
import { fetchBatchDeleteLog, fetchGetLogList } from '@/service/api';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { logDetailTypeRecord, logTypeRecord } from '@/constants/business';
import { useTable, useTableOperate } from '@/hooks/common/table';
import { useAuth } from '@/hooks/business/auth';
import LogOperateDrawer from './modules/log-operate-drawer.vue';
import LogSearch from './modules/log-search.vue';

const appStore = useAppStore();

const { columns, columnChecks, data, getData, loading, mobilePagination, searchParams, resetSearchParams } = useTable({
  apiFn: fetchGetLogList,
  showTotal: true,
  apiParams: {
    current: 1,
    size: 10,
    // if you want to use the searchParams in Form, you need to define the following properties, and the value is null
    // the value can not be undefined, otherwise the property in Form will not be reactive
    logType: '1',
    logUser: null,
    logDetailType: null,
    requestUrl: null,
    createTime: null,
    responseCode: null
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
      key: 'requestUrl',
      title: $t('page.manage.log.requestUrl'),
      align: 'center',
      width: 300
    },
    {
      key: 'logUser',
      title: $t('page.manage.log.logUser'),
      align: 'center',
      width: 100
    },
    {
      key: 'logDetailType',
      title: $t('page.manage.log.logDetailType'),
      align: 'center',
      minWidth: 50,
      render: row => {
        if (row.logDetailType) {
          const label = $t(logDetailTypeRecord[row.logDetailType]);
          return <NTag type="default">{label}</NTag>;
        }
        return null;
      }
    },
    {
      key: 'logType',
      title: $t('page.manage.log.logType'),
      align: 'center',
      width: 100,
      render: row => {
        const tagMap: Record<Api.SystemManage.logTypes, NaiveUI.ThemeColor> = {
          1: 'default',
          2: 'error',
          3: 'primary',
          4: 'info'
        };

        const label = $t(logTypeRecord[row.logType]);

        return <NTag type={tagMap[row.logType]}>{label}</NTag>;
      }
    },
    {
      key: 'createTime',
      title: $t('page.manage.log.createTime'),
      align: 'center',
      width: 200
    },
    {
      key: 'responseCode',
      title: $t('page.manage.log.responseCode'),
      align: 'center',
      width: 100
    },
    {
      key: 'operate',
      title: $t('common.operate'),
      align: 'center',
      width: 130,
      render: row => (
        <div class="flex-center gap-8px">
          <NButton type="primary" ghost size="small" onClick={() => edit(row.id)}>
            {$t('common.view')}
          </NButton>
        </div>
      )
    }
  ],
  transformer: res => {
    const { records = [], current = 1, size = 10, total = 0 } = res.data || {};

    const recordsWithIndex = records.map((item, index) => {
      return {
        ...item,
        index: total - (current - 1) * size + index // 倒序展示index
      };
    });

    return {
      data: recordsWithIndex,
      pageNum: current,
      pageSize: size,
      total
    };
  }
});

const {
  drawerVisible,
  operateType,
  checkedRowKeys,
  onBatchDeleted,
  editingData,
  handleEdit
  // closeDrawer
} = useTableOperate(data, getData);
const { hasAuth } = useAuth();

async function handleadd() {
  // request
  window.$message?.error('Not supported');
}

async function handleBatchDelete() {
  // request
  const { error } = await fetchBatchDeleteLog({ ids: checkedRowKeys.value });
  if (!error) {
    onBatchDeleted();
  }
}

function edit(id: number) {
  handleEdit(id);
}
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <LogSearch v-model:model="searchParams" @reset="resetSearchParams" @search="getData" />
    <NCard :title="$t('page.manage.log.title')" :bordered="false" size="small" class="sm:flex-1-hidden card-wrapper">
      <template #header-extra>
        <TableHeaderOperation
          v-model:columns="columnChecks"
          :disabled-delete="checkedRowKeys.length === 0"
          :loading="loading"
          @add="handleadd"
          @delete="handleBatchDelete"
          @refresh="getData"
        >
          <template #default><span v-if="!hasAuth('B_Add_Del_Batch-del')"></span></template>
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
      <LogOperateDrawer
        v-model:visible="drawerVisible"
        :operate-type="operateType"
        :row-data="editingData"
        @submitted="getData"
      />
    </NCard>
  </div>
</template>

<style scoped></style>
