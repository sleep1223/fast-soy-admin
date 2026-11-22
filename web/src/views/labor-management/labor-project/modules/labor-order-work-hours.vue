<script setup lang="ts">
import { computed, h, onBeforeUnmount, ref, watch } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { fetchAddLaborWorkHour, fetchGetLaborWorkHourList, fetchOcrRecognize } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import AssignmentStatusTag from '../../labor-work-hour/modules/assignment-status-tag.vue';

const props = withDefaults(defineProps<{ orderNo: string; skipPainting?: boolean }>(), { skipPainting: false });
const { hasAuth } = useAuth();
const records = ref<Api.LaborManagementManage.LaborWorkHour[]>([]);
const loading = ref(false);
const failed = ref(false);
const ticketCode = ref('');
const workHours = ref<number | null>(null);
const saving = ref(false);
const ocrLoading = ref(false);
const draggingTicketImage = ref(false);
const ticketImageInput = ref<HTMLInputElement | null>(null);
const ocrOptions = ref<{ label: string; value: string }[]>([]);
let requestSequence = 0;
let ocrSession = 0;

async function recognizeTicketImage(file: File | undefined) {
  if (!file || saving.value || ocrLoading.value) return;
  const supported =
    ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type) ||
    /\.(jpe?g|png|gif|webp)$/i.test(file.name);
  if (!supported || !file.size || file.size > 10 * 1024 * 1024) {
    window.$message?.warning($t('ocrTools.invalid', { size: 10 }));
    return;
  }
  const current = ++ocrSession;
  ocrLoading.value = true;
  ocrOptions.value = [];
  try {
    const { data, error } = await fetchOcrRecognize(file, { useCls: true });
    if (current !== ocrSession) return;
    if (error || !data) {
      window.$message?.error($t('ocrTools.failed'));
      return;
    }
    ocrOptions.value = [
      ...new Set(data.items.map(item => item.text.trim()).filter(value => value && value.length <= 100))
    ].map(value => ({
      label: value,
      value
    }));
    if (ocrOptions.value.length === 1) ticketCode.value = ocrOptions.value[0].value;
    if (!ocrOptions.value.length) window.$message?.warning($t('page.labor_management.labor_work_hour.ocrEmpty'));
  } catch {
    if (current === ocrSession) window.$message?.error($t('ocrTools.failed'));
  } finally {
    if (current === ocrSession) ocrLoading.value = false;
  }
}

function handleTicketImageChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const [file] = Array.from(input.files ?? []);
  input.value = '';
  void recognizeTicketImage(file);
}

function handleTicketImageDrop(event: DragEvent) {
  draggingTicketImage.value = false;
  const transfer = event.dataTransfer;
  const files = Array.from(transfer?.files ?? []);
  const droppedItems = Array.from(transfer?.items ?? [])
    .map(item => (item.kind === 'file' ? item.getAsFile() : null))
    .filter((item): item is File => item !== null);
  const file = [...files, ...droppedItems].find(
    item => item.type.startsWith('image/') || /\.(jpe?g|png|gif|webp)$/i.test(item.name)
  );
  if (!file) {
    window.$message?.warning($t('ocrTools.dropUnavailable'));
    return;
  }
  void recognizeTicketImage(file);
}

const columns = computed<DataTableColumns<Api.LaborManagementManage.LaborWorkHour>>(() => [
  { key: 'ticketCode', title: $t('page.labor_management.labor_work_hour.ticketCode'), minWidth: 160 },
  { key: 'workHours', title: $t('page.labor_management.labor_work_hour.workHours'), minWidth: 120 },
  {
    key: 'allocationMonth',
    title: $t('page.labor_management.labor_work_hour.allocationMonth'),
    minWidth: 120,
    render: row => row.allocationMonth?.slice(0, 7) ?? '—'
  },
  {
    key: 'assignmentStatus',
    title: $t('page.labor_management.labor_work_hour.assignmentStatus'),
    minWidth: 110,
    render: row => h(AssignmentStatusTag, { workerId: row.workerId, allocationMonth: row.allocationMonth })
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
      const { data, error } = await fetchGetLaborWorkHourList({ current: page, size: 1000, orderNos: [orderNo] });
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
  if (saving.value || props.skipPainting || !hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')) return;
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
    ocrSession += 1;
    ocrLoading.value = false;
    ocrOptions.value = [];
    draggingTicketImage.value = false;
    ticketCode.value = '';
    workHours.value = null;
    loadWorkHours();
  },
  { immediate: true }
);
onBeforeUnmount(() => {
  requestSequence += 1;
  ocrSession += 1;
});
</script>

<template>
  <div class="px-12px py-8px">
    <NForm
      v-if="!props.skipPainting && hasAuth('B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE')"
      inline
      @submit.prevent="addWorkHour"
    >
      <NFormItem :label="$t('page.labor_management.labor_work_hour.ticketCode')" required>
        <div
          class="w-full rounded-6px border border-dashed p-8px transition-colors"
          :class="draggingTicketImage ? 'border-primary bg-primary/5' : 'border-gray-300'"
          @dragover.prevent="draggingTicketImage = true"
          @dragleave.prevent="draggingTicketImage = false"
          @drop.prevent="handleTicketImageDrop"
        >
          <NInput
            v-model:value="ticketCode"
            :maxlength="100"
            :disabled="saving"
            :placeholder="$t('page.labor_management.labor_work_hour.form.ticketCode')"
          />
          <div class="mt-6px flex items-center justify-between gap-8px">
            <span class="text-12px text-gray-400">{{ $t('page.labor_management.labor_project.ticketDropHint') }}</span>
            <NButton size="tiny" :loading="ocrLoading" :disabled="saving" @click="ticketImageInput?.click()">
              {{ $t('page.labor_management.labor_work_hour.ocrUpload') }}
            </NButton>
          </div>
          <input
            ref="ticketImageInput"
            type="file"
            accept="image/*"
            class="hidden"
            :disabled="ocrLoading"
            @change="handleTicketImageChange"
          />
        </div>
        <NSelect
          v-if="ocrOptions.length"
          class="mt-6px"
          :options="ocrOptions"
          :placeholder="$t('page.labor_management.labor_work_hour.ocrSelect')"
          @update:value="value => (ticketCode = value)"
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
          :scroll-x="510"
          size="small"
        />
      </template>
    </NSpin>
  </div>
</template>
