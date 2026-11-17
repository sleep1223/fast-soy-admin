<script setup lang="tsx">
import { reactive, ref } from 'vue';
import { NButton, NPopconfirm, NSpace, NSwitch } from 'naive-ui';
import {
  fetchAddWorker,
  fetchDeleteWorker,
  fetchExportWorker,
  fetchGetWorkerList,
  fetchImportWorker,
  fetchPreviewImportWorker,
  fetchUpdateWorker,
  fetchWorkerImportTemplate
} from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';

defineOptions({ name: 'WorkTicketMasterData' });

const { hasAuth } = useAuth();
const workers = ref<Api.WorkTicketManagementManage.Worker[]>([]);
const loading = ref(false);
const keyword = ref('');
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onUpdatePage: (page: number) => {
    pagination.page = page;
    void loadWorkers();
  },
  onUpdatePageSize: (size: number) => {
    pagination.pageSize = size;
    pagination.page = 1;
    void loadWorkers();
  }
});

async function loadWorkers() {
  loading.value = true;
  const { data, error } = await fetchGetWorkerList({
    current: pagination.page,
    size: pagination.pageSize,
    name: keyword.value || null,
    workerNo: keyword.value || null
  });
  loading.value = false;
  if (!error && data) {
    workers.value = data.records;
    pagination.itemCount = data.total;
  }
}

const formVisible = ref(false);
const form = reactive<{ id?: string; workerNo: string; name: string; enabled: boolean; remark: string }>({
  id: undefined,
  workerNo: '',
  name: '',
  enabled: true,
  remark: ''
});

function addWorker() {
  Object.assign(form, { id: undefined, workerNo: '', name: '', enabled: true, remark: '' });
  formVisible.value = true;
}

function editWorker(row: Api.WorkTicketManagementManage.Worker) {
  Object.assign(form, {
    id: row.id,
    workerNo: row.workerNo ?? '',
    name: row.name,
    enabled: row.enabled ?? true,
    remark: row.remark ?? ''
  });
  formVisible.value = true;
}

async function saveWorker() {
  const payload = {
    ...form,
    workerNo: form.workerNo || null,
    productionUnitId: null
  };
  const { error } = form.id
    ? await fetchUpdateWorker({ ...payload, id: form.id })
    : await fetchAddWorker(payload);
  if (error) return;
  formVisible.value = false;
  await loadWorkers();
}

async function removeWorker(id: string) {
  const { error } = await fetchDeleteWorker({ id });
  if (!error) await loadWorkers();
}

const columns = [
  { key: 'workerNo', title: $t('page.work_ticket_management.worker.workerNo'), width: 160 },
  { key: 'name', title: $t('page.work_ticket_management.worker.name'), minWidth: 180 },
  {
    key: 'enabled',
    title: $t('page.work_ticket_management.worker.enabled'),
    width: 120,
    render: (row: Api.WorkTicketManagementManage.Worker) =>
      row.enabled ? $t('page.work_ticket_management.workflow.enabled') : $t('page.work_ticket_management.workflow.disabled')
  },
  {
    key: 'actions',
    title: $t('page.work_ticket_management.workflow.actions'),
    width: 150,
    render: (row: Api.WorkTicketManagementManage.Worker) => (
      <NSpace size={8}>
        <NButton size="small" disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_WORKER_EDIT')} onClick={() => editWorker(row)}>
          {$t('common.edit')}
        </NButton>
        <NPopconfirm onPositiveClick={() => removeWorker(row.id)}>
          {{
            default: () => $t('common.confirmDelete'),
            trigger: () => (
              <NButton size="small" type="error" ghost disabled={!hasAuth('B_WORK_TICKET_MANAGEMENT_WORKER_DELETE')}>
                {$t('common.delete')}
              </NButton>
            )
          }}
        </NPopconfirm>
      </NSpace>
    )
  }
];

void loadWorkers();
</script>

<template>
  <NCard :title="$t('page.work_ticket_management.worker.pageTitle')" :bordered="false" size="small">
    <NSpace class="mb-12px" align="center" wrap>
      <NInput
        v-model:value="keyword"
        clearable
        :placeholder="$t('page.work_ticket_management.workflow.search')"
        class="w-220px"
        @keyup.enter="loadWorkers"
      />
      <NButton size="small" @click="loadWorkers">{{ $t('page.work_ticket_management.workflow.search') }}</NButton>
      <NButton
        size="small"
        type="primary"
        :disabled="!hasAuth('B_WORK_TICKET_MANAGEMENT_WORKER_CREATE')"
        @click="addWorker"
      >
        {{ $t('page.work_ticket_management.workflow.addWorker') }}
      </NButton>
      <ExcelTransfer
        :import-api="fetchImportWorker"
        :preview-api="fetchPreviewImportWorker"
        :export-api="() => fetchExportWorker({ current: 1, size: 1000 })"
        :template-api="fetchWorkerImportTemplate"
        @imported="loadWorkers"
      />
    </NSpace>
    <NDataTable
      :columns="columns"
      :data="workers"
      :loading="loading"
      remote
      :pagination="pagination"
      :row-key="row => row.id"
      size="small"
    />

    <NModal
      v-model:show="formVisible"
      preset="card"
      :title="
        form.id
          ? $t('page.work_ticket_management.worker.editWorker')
          : $t('page.work_ticket_management.worker.addWorker')
      "
      class="w-500px max-w-95vw"
    >
      <NForm label-placement="top">
        <NFormItem :label="$t('page.work_ticket_management.worker.workerNo')">
          <NInput v-model:value="form.workerNo" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.name')" required>
          <NInput v-model:value="form.name" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.enabled')">
          <NSwitch v-model:value="form.enabled" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.remark')">
          <NInput v-model:value="form.remark" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton @click="formVisible = false">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="saveWorker">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NModal>
  </NCard>
</template>
