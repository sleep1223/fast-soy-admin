<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { fetchAddLaborWorkHour, fetchGetLaborWorkHourList } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';

const props = defineProps<{ orderNo: string }>();
const { hasAuth } = useAuth();
const records = ref<Api.LaborManagementManage.LaborWorkHour[]>([]);
const loading = ref(false);
const failed = ref(false);
const ticketCode = ref('');
const workHours = ref<number | null>(null);
const saving = ref(false);
let requestSequence = 0;

const columns = computed<DataTableColumns<Api.LaborManagementManage.LaborWorkHour>>(() => [
  { key: 'ticketCode', title: $t('page.labor_management.labor_work_hour.ticketCode'), minWidth: 160 },
  { key: 'workHours', title: $t('page.labor_management.labor_work_hour.workHours'), minWidth: 120 },
  {
    key: 'allocationMonth',
    title: $t('page.labor_management.labor_work_hour.allocationMonth'),
    minWidth: 120,
    render: row => row.allocationMonth?.slice(0, 7) ?? '—'
  }
]);

async function loadWorkHours() {
  const current = ++requestSequence;
  const orderNo = props.orderNo;
  loading.value = true;
  failed.value = false;
  records.value = [];
  const matches: Api.LaborManagementManage.LaborWorkHour[] = [];
  let page = 1;
  let received = 0;
  let total = 0;
  try {
    do {
      const { data, error } = await fetchGetLaborWorkHourList({ current: page, size: 1000, orderNo });
      if (current !== requestSequence) return;
      if (error || !data) {
        failed.value = true;
        return;
      }
      matches.push(...data.records.filter(item => item.orderNo === orderNo));
      received += data.records.length;
      total = data.total;
      if (!data.records.length) break;
      page += 1;
    } while (received < total);
    records.value = matches;
  } catch {
    if (current === requestSequence) failed.value = true;
  } finally {
    if (current === requestSequence) loading.value = false;
  }
}

async function addWorkHour() {
  if (saving.value || !hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')) return;
  const code = ticketCode.value.trim();
  if (!code || code.length > 100) {
    window.$message?.warning($t('page.labor_management.labor_project.ticketCodeRequired'));
    return;
  }
  if (workHours.value === null || !Number.isFinite(workHours.value) || workHours.value < 0) {
    window.$message?.warning($t('page.labor_management.labor_project.workHoursRequired'));
    return;
  }
  const orderNo = props.orderNo;
  saving.value = true;
  try {
    const { error } = await fetchAddLaborWorkHour({ ticketCode: code, workHours: workHours.value, orderNo });
    if (error || orderNo !== props.orderNo) return;
    ticketCode.value = '';
    workHours.value = null;
    window.$message?.success($t('common.addSuccess'));
    await loadWorkHours();
  } catch {
    window.$message?.error($t('page.labor_management.labor_project.createWorkHourFailed'));
  } finally {
    saving.value = false;
  }
}

watch(
  () => props.orderNo,
  () => {
    ticketCode.value = '';
    workHours.value = null;
    loadWorkHours();
  },
  { immediate: true }
);
onBeforeUnmount(() => {
  requestSequence += 1;
});
</script>

<template>
  <div class="px-12px py-8px">
    <NForm v-if="hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')" inline @submit.prevent="addWorkHour">
      <NFormItem :label="$t('page.labor_management.labor_work_hour.ticketCode')" required>
        <NInput
          v-model:value="ticketCode"
          :maxlength="100"
          :disabled="saving"
          :placeholder="$t('page.labor_management.labor_work_hour.form.ticketCode')"
        />
      </NFormItem>
      <NFormItem :label="$t('page.labor_management.labor_work_hour.workHours')" required>
        <NInputNumber
          v-model:value="workHours"
          :min="0"
          :precision="2"
          :disabled="saving"
          :placeholder="$t('page.labor_management.labor_work_hour.form.workHours')"
        />
      </NFormItem>
      <NFormItem>
        <NButton type="primary" attr-type="submit" :loading="saving">{{ $t('common.add') }}</NButton>
      </NFormItem>
    </NForm>
    <NSpin :show="loading">
      <NAlert v-if="failed" type="error">
        {{ $t('page.labor_management.labor_project.workHoursLoadFailed') }}
        <NButton text type="primary" class="ml-8px" @click="loadWorkHours">
          {{ $t('page.labor_management.labor_project.retryOrders') }}
        </NButton>
      </NAlert>
      <NEmpty
        v-else-if="!loading && !records.length"
        :description="$t('page.labor_management.labor_project.noMatchedWorkHours')"
      />
      <template v-else-if="records.length">
        <div class="mb-8px font-medium">
          {{ $t('page.labor_management.labor_project.matchedWorkHours') }} · {{ records.length }}
        </div>
        <NDataTable
          :columns="columns"
          :data="records"
          :row-key="row => row.id"
          :pagination="{ pageSize: 10 }"
          :scroll-x="400"
          size="small"
        />
      </template>
    </NSpin>
  </div>
</template>
