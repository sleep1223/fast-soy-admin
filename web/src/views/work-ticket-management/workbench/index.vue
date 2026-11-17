<script setup lang="ts">
import { computed, h, onMounted, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import type { DataTableColumns, UploadCustomRequestOptions } from 'naive-ui';
import { NButton, NTag } from 'naive-ui';
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';
import {
  fetchCreateTicket,
  fetchImportCommit,
  fetchImportPreview,
  fetchImportRows,
  fetchOpenWorkMonth,
  fetchOrderCandidates,
  fetchProductionUnitOptions,
  fetchTimeBatchSave,
  fetchTickets,
  fetchWorkerOptions
} from '@/service/api';
import MonthUnitToolbar from '../shared/month-unit-toolbar.vue';

defineOptions({ name: 'WorkTicketWorkbench' });

const month = ref(dayjs().format('YYYY-MM'));
const units = ref<Api.WorkTicketManagement.UnitOption[]>([]);
const unitId = ref<string | null>(null);
const workMonthId = ref<string | null>(null);
const loading = ref(false);
const rows = ref<Api.WorkTicketManagement.ImportRow[]>([]);
const total = ref(0);
const keyword = ref('');
const page = reactive({ current: 1, size: 20 });
const selectedRow = ref<Api.WorkTicketManagement.ImportRow | null>(null);
const candidates = ref<Api.WorkTicketManagement.OrderCandidate[]>([]);
const tickets = ref<Api.WorkTicketManagement.Ticket[]>([]);
const workers = ref<Api.WorkTicketManagement.WorkerOption[]>([]);
const onlyUnassigned = ref(false);

async function loadUnits() {
  const { data } = await fetchProductionUnitOptions();
  units.value = data ?? [];
  if (!unitId.value && units.value.length) unitId.value = units.value[0].id;
}

async function openMonth() {
  if (!unitId.value) return;
  loading.value = true;
  const { data, error } = await fetchOpenWorkMonth({ yearMonth: month.value, productionUnitId: unitId.value });
  loading.value = false;
  if (error || !data) return;
  workMonthId.value = data.id;
  await Promise.all([loadRows(), loadWorkers()]);
}

async function loadRows() {
  if (!workMonthId.value) return;
  loading.value = true;
  const { data, error } = await fetchImportRows({
    workMonthId: workMonthId.value,
    sourceType: null,
    matchStatus: null,
    keyword: keyword.value.trim() || null,
    current: page.current,
    size: page.size
  });
  loading.value = false;
  if (!error && data) {
    rows.value = data.records;
    total.value = data.total;
    if (selectedRow.value && !rows.value.some(row => row.id === selectedRow.value?.id)) {
      selectedRow.value = null;
      candidates.value = [];
      tickets.value = [];
    }
  }
}

async function loadWorkers() {
  const { data } = await fetchWorkerOptions();
  workers.value = data ?? [];
}

async function selectProject(row: Api.WorkTicketManagement.ImportRow) {
  selectedRow.value = row;
  candidates.value = [];
  tickets.value = [];
  if (!workMonthId.value) return;
  loading.value = true;
  const [ordersResult, ticketsResult] = await Promise.all([
    fetchOrderCandidates({
      workMonthId: workMonthId.value,
      partNo: row.normalizedPartNo || row.rawPartNo,
      limit: 100,
      includeOtherUnits: true,
      includePartial: false
    }),
    fetchTickets({ workMonthId: workMonthId.value, current: 1, size: 1000 })
  ]);
  loading.value = false;
  candidates.value = ordersResult.data ?? [];
  const orderIds = new Set(candidates.value.map(order => order.id));
  tickets.value = (ticketsResult.data?.records ?? []).filter(ticket => orderIds.has(ticket.orderId ?? ''));
}

const columns: DataTableColumns<Api.WorkTicketManagement.ImportRow> = [
  { title: '项目号', key: 'normalizedPartNo', minWidth: 180 },
  {
    title: '来源',
    key: 'sourceType',
    width: 100,
    render: row => (row.sourceType === 'actual' ? '补录' : '初始清单')
  },
  {
    title: '订单匹配',
    key: 'matchStatus',
    width: 120,
    render: row =>
      h(
        NTag,
        { type: row.matchStatus === 'matched' ? 'success' : 'warning', bordered: false },
        {
          default: () =>
            row.matchStatus === 'matched'
              ? '已匹配'
              : row.matchStatus === 'ambiguous'
                ? '多个订单'
                : row.matchStatus === 'missing'
                  ? '无订单'
                  : row.matchStatus
        }
      )
  },
  { title: '订单号', key: 'orderNo', minWidth: 140, render: row => row.orderNo || '点击查看订单' },
  {
    title: '操作',
    key: 'actions',
    width: 110,
    render: row =>
      h(
        NButton,
        { size: 'small', type: 'primary', secondary: true, onClick: () => void selectProject(row) },
        { default: () => '查看订单' }
      )
  }
];

// Import one initial list, then supplement it. The backend deduplicates both
// sources on normalized project number, so a supplement never adds an existing number.
const importVisible = ref(false);
const importSource = ref<Api.WorkTicketManagement.ImportSourceType>('plan');
const importFile = ref<File | null>(null);
const importPreview = ref<Api.WorkTicketManagement.ImportPreview | null>(null);
const importBusy = ref(false);
function openImport(source: Api.WorkTicketManagement.ImportSourceType) {
  importSource.value = source;
  importFile.value = null;
  importPreview.value = null;
  importVisible.value = true;
}
async function previewFile(options: UploadCustomRequestOptions) {
  if (!options.file.file || !workMonthId.value) return options.onError();
  importBusy.value = true;
  const { data, error } = await fetchImportPreview(options.file.file, workMonthId.value, importSource.value);
  importBusy.value = false;
  if (error || !data) return options.onError();
  importFile.value = options.file.file;
  importPreview.value = data;
  options.onFinish();
}
async function commitImport() {
  if (!importFile.value || !workMonthId.value) return;
  importBusy.value = true;
  const { data, error } = await fetchImportCommit(importFile.value, workMonthId.value, importSource.value);
  importBusy.value = false;
  if (error || !data) return;
  importVisible.value = false;
  window.$message?.success(`新增 ${data.rowCount} 个项目号，跳过重复 ${data.duplicateRows} 个`);
  page.current = 1;
  await loadRows();
}

const ticketVisible = ref(false);
const ticketSaving = ref(false);
const selectedOrder = ref<Api.WorkTicketManagement.OrderCandidate | null>(null);
const ticketForm = reactive({
  code: '',
  workerId: null as string | null,
  workDate: dayjs().format('YYYY-MM-DD'),
  hours: null as number | null,
  codeSource: 'manual'
});
function openTicket(order: Api.WorkTicketManagement.OrderCandidate) {
  selectedOrder.value = order;
  Object.assign(ticketForm, {
    code: '',
    workerId: null,
    workDate: dayjs().format('YYYY-MM-DD'),
    hours: null,
    codeSource: 'manual'
  });
  ticketVisible.value = true;
}
async function copyOrderNo(orderNo: string) {
  try {
    await navigator.clipboard.writeText(orderNo);
    window.$message?.success('订单号已复制');
  } catch {
    window.$message?.error('复制失败，请手动选择订单号');
  }
}
function onOcrRecognized(result: Api.Ocr.Result) {
  ticketForm.code = result.text.trim();
  ticketForm.codeSource = 'ocr';
}
async function saveTicket() {
  if (!workMonthId.value || !selectedRow.value || !selectedOrder.value) return;
  if (!ticketForm.code.trim()) {
    window.$message?.warning('请先录入工票码');
    return;
  }
  if (ticketForm.hours !== null && (!ticketForm.workerId || !ticketForm.workDate)) {
    window.$message?.warning('登记工时需要选择人员和工作日期');
    return;
  }
  ticketSaving.value = true;
  const { data: ticket, error } = await fetchCreateTicket({
    workMonthId: workMonthId.value,
    orderId: selectedOrder.value.id,
    sourceImportRowId: selectedRow.value.id,
    partNoSnapshot: selectedOrder.value.partNo,
    nameSnapshot: selectedOrder.value.name,
    ticketCode: ticketForm.code.trim() || null,
    codeSource: ticketForm.codeSource,
    workerIds: ticketForm.workerId ? [ticketForm.workerId] : [],
    allowAddMapping: true
  });
  if (error || !ticket) {
    ticketSaving.value = false;
    return;
  }
  if (ticketForm.hours !== null && ticketForm.workerId) {
    const { error: timeError } = await fetchTimeBatchSave({
      workMonthId: workMonthId.value,
      entries: [
        {
          ticketId: ticket.id,
          workerId: ticketForm.workerId,
          workDate: ticketForm.workDate,
          hours: String(ticketForm.hours),
          revision: ticket.revision
        }
      ]
    });
    if (timeError) {
      ticketSaving.value = false;
      ticketVisible.value = false;
      await selectProject(selectedRow.value);
      window.$message?.error('工票已保存，但工时没有保存；请在工时登记中补录');
      return;
    }
  }
  ticketSaving.value = false;
  ticketVisible.value = false;
  await selectProject(selectedRow.value);
  window.$message?.success('工票记录已保存');
}

const visibleTickets = computed(() =>
  onlyUnassigned.value ? tickets.value.filter(ticket => ticket.assignmentCount === 0) : tickets.value
);
const ticketColumns: DataTableColumns<Api.WorkTicketManagement.Ticket> = [
  { title: '工票码', key: 'ticketCode', render: ticket => ticket.ticketCode || '未填写' },
  { title: '人员', key: 'workerNames', render: ticket => ticket.workerNames.join('、') || '未分配' },
  { title: '工时', key: 'totalHours', render: ticket => `${ticket.totalHours} 小时` }
];
const previewColumns: DataTableColumns<Api.WorkTicketManagement.ImportPreviewRow> = [
  { title: '项目号', key: 'rawPartNo' },
  {
    title: '订单号',
    key: 'orderNo',
    render: row => row.orderNo || (row.duplicateOfRowId ? '重复，提交时跳过' : '未匹配')
  },
  { title: '备注', key: 'note' }
];

onMounted(async () => {
  await loadUnits();
});
watch([month, unitId], () => void openMonth());
</script>

<template>
  <div class="flex-col gap-16px">
    <MonthUnitToolbar v-model:month="month" v-model:unit-id="unitId" :units="units" :loading="loading">
      <NButton type="primary" :disabled="!workMonthId" @click="openImport('plan')">导入当月件号</NButton>
      <NButton :disabled="!workMonthId" @click="openImport('actual')">补录遗漏件号</NButton>
    </MonthUnitToolbar>

    <NGrid cols="1 900:2" :x-gap="16" :y-gap="16" responsive="screen">
      <NGi>
        <NCard title="当月项目号" :bordered="false" size="small">
          <template #header-extra>
            <NSpace>
              <NInput
                v-model:value="keyword"
                clearable
                placeholder="搜索项目号"
                class="w-180px"
                @keyup.enter="loadRows"
              />
              <NButton @click="loadRows">搜索</NButton>
            </NSpace>
          </template>
          <NDataTable
            :columns="columns"
            :data="rows"
            :loading="loading"
            :row-key="row => row.id"
            :row-props="row => ({ onDblclick: () => selectProject(row) })"
            :pagination="{
              page: page.current,
              pageSize: page.size,
              itemCount: total,
              onUpdatePage: (value: number) => {
                page.current = value;
                loadRows();
              },
              onUpdatePageSize: (value: number) => {
                page.size = value;
                page.current = 1;
                loadRows();
              }
            }"
            size="small"
          />
          <div class="mt-8px text-12px text-gray">补录时项目号已存在会自动跳过。双击项目号也可查看订单。</div>
        </NCard>
      </NGi>

      <NGi>
        <NCard
          :title="selectedRow ? `项目号：${selectedRow.normalizedPartNo}` : '订单与工票'"
          :bordered="false"
          size="small"
        >
          <NEmpty v-if="!selectedRow" description="选择左侧项目号，查看对应订单" />
          <template v-else>
            <div class="mb-12px flex items-center justify-between">
              <span>匹配到 {{ candidates.length }} 个订单</span>
              <NSwitch v-model:value="onlyUnassigned">
                <template #checked>只看未分配</template>
                <template #unchecked>显示全部工票</template>
              </NSwitch>
            </div>
            <NEmpty v-if="!candidates.length" description="订单系统中没有找到相同项目号" />
            <div
              v-for="order in candidates"
              :key="order.id"
              class="mb-12px rounded border border-solid border-gray-200 p-12px"
            >
              <div class="flex items-start justify-between gap-8px">
                <div>
                  <div class="font-600">订单号：{{ order.orderNo }}</div>
                  <div class="mt-4px text-13px">{{ order.partNo }} · {{ order.name }}</div>
                  <div class="mt-4px text-12px text-gray">
                    数量 {{ order.quantity ?? '—' }} · 已入库 {{ order.receivedQuantity ?? '—' }}
                  </div>
                </div>
                <NSpace>
                  <NButton size="small" @click="copyOrderNo(order.orderNo)">复制订单号</NButton>
                  <NButton size="small" type="primary" @click="openTicket(order)">录入工票 / 工时</NButton>
                </NSpace>
              </div>
              <NDivider />
              <NEmpty
                v-if="!visibleTickets.filter(ticket => ticket.orderId === order.id).length"
                description="还没有工票记录"
                size="small"
              />
              <NDataTable
                v-else
                :columns="ticketColumns"
                :data="visibleTickets.filter(ticket => ticket.orderId === order.id)"
                :row-key="ticket => ticket.id"
                size="small"
              />
            </div>
          </template>
        </NCard>
      </NGi>
    </NGrid>

    <NModal
      v-model:show="importVisible"
      preset="card"
      :title="importSource === 'plan' ? '导入当月件号' : '补录遗漏件号'"
      class="w-760px"
    >
      <NSpace vertical>
        <div>选择 Excel 文件，只需要包含一列项目号。补录文件中已存在的项目号会跳过。</div>
        <NUpload accept=".xlsx" :max="1" :custom-request="previewFile" :show-file-list="true">
          <NButton :loading="importBusy">选择 .xlsx 文件并预览</NButton>
        </NUpload>
        <template v-if="importPreview">
          <NAlert type="info" :show-icon="false">
            共 {{ importPreview.totalRows }} 行；新增候选
            {{ importPreview.totalRows - importPreview.duplicateRows - importPreview.invalidRows }}，重复跳过
            {{ importPreview.duplicateRows }}，无效 {{ importPreview.invalidRows }}。
          </NAlert>
          <NDataTable :columns="previewColumns" :data="importPreview.rows" :max-height="320" size="small" />
          <NButton type="primary" :loading="importBusy" @click="commitImport">确认导入</NButton>
        </template>
      </NSpace>
    </NModal>

    <NModal v-model:show="ticketVisible" preset="card" title="录入工票与工时" class="w-560px">
      <NForm label-placement="top">
        <NFormItem label="订单号"><NInput :value="selectedOrder?.orderNo" readonly /></NFormItem>
        <NFormItem label="工票码" required>
          <NInput v-model:value="ticketForm.code" placeholder="粘贴工票码" />
        </NFormItem>
        <NFormItem label="工票照片识别"><OcrRecognizer @recognized="onOcrRecognized" /></NFormItem>
        <NFormItem label="人员">
          <NSelect
            v-model:value="ticketForm.workerId"
            :options="workers.map(worker => ({ label: worker.name, value: worker.id }))"
            clearable
            filterable
            placeholder="暂不分配可留空"
          />
        </NFormItem>
        <NFormItem label="工作日期">
          <NDatePicker
            v-model:formatted-value="ticketForm.workDate"
            type="date"
            value-format="yyyy-MM-dd"
            class="w-full"
          />
        </NFormItem>
        <NFormItem label="工时（小时）">
          <NInputNumber
            v-model:value="ticketForm.hours"
            :min="0.01"
            :max="24"
            :precision="2"
            clearable
            class="w-full"
            placeholder="可稍后登记"
          />
        </NFormItem>
        <NButton type="primary" :loading="ticketSaving" @click="saveTicket">保存</NButton>
      </NForm>
    </NModal>
  </div>
</template>
