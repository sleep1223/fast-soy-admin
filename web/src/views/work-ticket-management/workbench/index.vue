<script setup lang="ts">
import { computed, onMounted, reactive, ref, shallowRef } from 'vue';
import dayjs from 'dayjs';
import ExcelImportPreview from '@/components/advanced/excel-import-preview.vue';
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import {
  fetchAddWorkAssetAllocation,
  fetchAddWorkAssetTicket,
  fetchGetWorkProjectList,
  fetchGetWorkProjectOrderList,
  fetchImportWorkProject,
  fetchPreviewImportWorkProject,
  fetchUpdateWorkAssetAllocation,
  fetchUpdateWorkAssetTicket,
  fetchWorkAssetTickets
} from '@/service/api/work_ticket_management-assets';
import type {
  AssetAllocation,
  AssetOrder,
  AssetProject,
  AssetTicket,
  TicketInput
} from '@/service/api/work_ticket_management-assets';
import { fetchWorkerOptions } from '@/service/api/work_ticket_management-workflow';
import type { ExcelImportOptions } from '@/utils/excel';
import AssetReport from './asset-report.vue';

defineOptions({ name: 'WorkTicketWorkbench' });

const { hasAuth } = useAuth();
const canImport = computed(() => hasAuth('B_WORK_TICKET_MANAGEMENT_IMPORT_PLAN'));
const canEditTickets = computed(() => hasAuth('B_WORK_TICKET_MANAGEMENT_TICKET_CREATE'));
const canUseOcr = computed(() => hasAuth('B_WORK_TICKET_MANAGEMENT_TICKET_OCR'));
const canAllocate = computed(() => hasAuth('B_WORK_TICKET_MANAGEMENT_TIME_EDIT'));
const t = (key: string) => $t(`page.work_ticket_management.assets.${key}` as const);

const pageSize = 15;
const keyword = ref('');
const projectPage = ref(1);
const projectTotal = ref(0);
const projects = shallowRef<AssetProject[]>([]);
const project = shallowRef<AssetProject | null>(null);
const orderPage = ref(1);
const orderTotal = ref(0);
const orders = shallowRef<AssetOrder[]>([]);
const order = shallowRef<AssetOrder | null>(null);
const tickets = shallowRef<AssetTicket[]>([]);
const loadingProjects = ref(false);
const loadingOrders = ref(false);
const loadingTickets = ref(false);
let projectRequest = 0;
let orderRequest = 0;
let ticketRequest = 0;

async function loadProjects(page = projectPage.value) {
  const requestId = ++projectRequest;
  projectPage.value = page;
  loadingProjects.value = true;
  const { data, error } = await fetchGetWorkProjectList({
    current: page,
    size: pageSize,
    partNo: keyword.value.trim()
  });
  if (requestId !== projectRequest) return;
  loadingProjects.value = false;
  if (error || !data) return;
  projects.value = data.records;
  projectTotal.value = data.total;
}

async function selectProject(item: AssetProject, page = 1, keepOrder = false) {
  const requestId = ++orderRequest;
  project.value = item;
  orderPage.value = page;
  if (!keepOrder) {
    ++ticketRequest;
    order.value = null;
    tickets.value = [];
    loadingTickets.value = false;
    orders.value = [];
    orderTotal.value = 0;
  }
  loadingOrders.value = true;
  const { data, error } = await fetchGetWorkProjectOrderList(item.id, { current: page, size: pageSize });
  if (requestId !== orderRequest) return;
  loadingOrders.value = false;
  if (error || !data) return;
  orders.value = data.records;
  orderTotal.value = data.total;
}

async function selectOrder(item: AssetOrder) {
  const requestId = ++ticketRequest;
  if (order.value?.id !== item.id) tickets.value = [];
  order.value = item;
  loadingTickets.value = true;
  const { data, error } = await fetchWorkAssetTickets(item.id);
  if (requestId !== ticketRequest) return;
  loadingTickets.value = false;
  if (!error && data) tickets.value = data;
}

const importFile = shallowRef<File | null>(null);

function readFile(event: Event) {
  const input = event.target as HTMLInputElement;
  importFile.value = input.files?.[0] ?? null;
  input.value = '';
}

async function importProjects(file: File, options?: ExcelImportOptions) {
  const result = await fetchImportWorkProject(file, options);
  if (!result.error && result.data) {
    const { matchedOrderCount, unmatchedProjectCount } = result.data;
    const summary = $t('page.work_ticket_management.assets.importResult', {
      orders: matchedOrderCount,
      projects: unmatchedProjectCount
    });
    window.$message?.info(summary);
    void loadProjects(1);
    if (project.value) void selectProject(project.value, orderPage.value, true);
  }
  return result;
}

async function copyOrder(orderNo: string) {
  try {
    await navigator.clipboard.writeText(orderNo);
    window.$message?.success(t('copied'));
  } catch {
    window.$message?.warning(t('copyFailed'));
  }
}

const editingTicket = shallowRef<AssetTicket | null>(null);
const ticketVisible = ref(false);
const ticketBusy = ref(false);
const showOcr = ref(false);
const ocrOptions = ref<{ label: string; value: string }[]>([]);
const ticketForm = reactive<TicketInput>({ ticketCode: '', codeSource: 'manual', totalHours: null });

function openTicket(item: AssetTicket | null = null) {
  editingTicket.value = item;
  ticketForm.ticketCode = item?.ticketCode ?? '';
  ticketForm.codeSource = item?.codeSource ?? 'manual';
  ticketForm.totalHours = item?.totalHours == null ? null : Number(item.totalHours);
  ocrOptions.value = [];
  showOcr.value = false;
  ticketVisible.value = true;
}

function ocrRecognized(result: Api.Ocr.Result) {
  const candidates = [
    ...new Set(result.items.map(item => item.text.trim()).filter(code => code && code.length <= 100))
  ];
  ocrOptions.value = candidates.map(code => ({ label: code, value: code }));
}

async function saveTicket() {
  const selected = order.value;
  if (!selected || !ticketForm.ticketCode.trim() || ticketBusy.value) return;
  ticketBusy.value = true;
  const { error } = editingTicket.value
    ? await fetchUpdateWorkAssetTicket(editingTicket.value.id, ticketForm)
    : await fetchAddWorkAssetTicket(selected.id, ticketForm);
  ticketBusy.value = false;
  if (error) return;
  ticketVisible.value = false;
  await selectOrder(selected);
  if (project.value) void selectProject(project.value, orderPage.value, true);
}

const allocation = shallowRef<{ ticket: AssetTicket; record: AssetAllocation | null } | null>(null);
const allocationBusy = ref(false);
const workerOptions = shallowRef<{ label: string; value: string }[]>([]);
const assignedWorker = ref<string | null>(null);
const assignedOn = ref<string | null>(null);
const assignedHours = ref<number | null>(null);

async function openAllocation(ticket: AssetTicket, record: AssetAllocation | null = null) {
  allocation.value = { ticket, record };
  assignedWorker.value = record?.workerId ?? null;
  assignedOn.value = record?.assignedOn ?? dayjs().format('YYYY-MM-DD');
  assignedHours.value = record?.hours == null ? null : Number(record.hours);
  const { data, error } = await fetchWorkerOptions();
  if (!error && data && allocation.value?.ticket.id === ticket.id && allocation.value.record === record) {
    const options = data.map(item => ({
      label: item.workerNo ? `${item.name} · ${item.workerNo}` : item.name,
      value: item.id
    }));
    if (record && !options.some(item => item.value === record.workerId)) {
      options.push({ label: record.workerName, value: record.workerId });
    }
    workerOptions.value = options;
  }
}

async function saveAllocation() {
  const target = allocation.value;
  const selected = order.value;
  if (!target || !selected || !assignedOn.value || !assignedWorker.value || allocationBusy.value) return;
  allocationBusy.value = true;
  const payload = { workerId: assignedWorker.value, assignedOn: assignedOn.value, hours: assignedHours.value };
  const { error } = target.record
    ? await fetchUpdateWorkAssetAllocation(target.ticket.id, target.record.id, payload)
    : await fetchAddWorkAssetAllocation(target.ticket.id, payload);
  allocationBusy.value = false;
  if (error) return;
  allocation.value = null;
  await selectOrder(selected);
}

onMounted(() => loadProjects());
</script>

<template>
  <NTabs type="line" animated class="min-h-0">
    <NTabPane name="assets" :tab="t('assets')">
      <div class="grid gap-16px xl:grid-cols-[18rem_minmax(0,1fr)]">
        <NCard :title="t('projects')" size="small">
          <template #header-extra>
            <label v-if="canImport" class="relative inline-block">
              <NButton tag="span" size="small" type="primary" secondary>{{ t('import') }}</NButton>
              <input
                type="file"
                accept=".xlsx"
                :aria-label="t('import')"
                class="absolute inset-0 size-full cursor-pointer opacity-0"
                @change="readFile"
              />
            </label>
          </template>

          <NInputGroup>
            <NInput v-model:value="keyword" clearable :placeholder="t('partNo')" @keyup.enter="loadProjects(1)" />
            <NButton @click="loadProjects(1)">{{ $t('common.search') }}</NButton>
          </NInputGroup>
          <NSpin :show="loadingProjects" class="my-12px">
            <NEmpty v-if="!projects.length" :description="t('emptyProjects')" />
            <NList v-else hoverable clickable>
              <NListItem v-for="item in projects" :key="item.id">
                <NButton
                  block
                  :type="project?.id === item.id ? 'primary' : 'default'"
                  :secondary="project?.id === item.id"
                  :quaternary="project?.id !== item.id"
                  @click="selectProject(item)"
                >
                  <span class="mr-8px max-w-150px truncate" :title="item.partNo">{{ item.partNo }}</span>
                  <NTag size="small" round>{{ item.orderCount }}</NTag>
                </NButton>
              </NListItem>
            </NList>
          </NSpin>
          <NPagination
            v-if="projectTotal > pageSize"
            :page="projectPage"
            :page-size="pageSize"
            :item-count="projectTotal"
            :page-slot="3"
            @update:page="loadProjects"
          />
        </NCard>

        <NSpace vertical :size="16" class="min-w-0">
          <NCard :title="project?.partNo ?? t('orders')" size="small">
            <NSpin :show="loadingOrders">
              <NEmpty v-if="!project" :description="t('selectProject')" />
              <NEmpty v-else-if="!orders.length" :description="t('emptyOrders')" />
              <div v-else class="overflow-x-auto">
                <NTable size="small" :single-line="false">
                  <thead>
                    <tr>
                      <th>{{ t('orderNo') }}</th>
                      <th>{{ t('orderName') }}</th>
                      <th>{{ t('tickets') }}</th>
                      <th>{{ $t('common.action') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in orders" :key="item.id">
                      <td class="font-mono">{{ item.orderNo }}</td>
                      <td>{{ item.name }}</td>
                      <td>{{ item.ticketCount }}</td>
                      <td>
                        <NSpace :wrap="false">
                          <NButton size="tiny" secondary @click="copyOrder(item.orderNo)">{{ t('copyOrder') }}</NButton>
                          <NButton
                            size="tiny"
                            :type="order?.id === item.id ? 'primary' : 'default'"
                            @click="selectOrder(item)"
                          >
                            {{ t('viewTickets') }}
                          </NButton>
                        </NSpace>
                      </td>
                    </tr>
                  </tbody>
                </NTable>
              </div>
            </NSpin>
            <NPagination
              v-if="project && orderTotal > pageSize"
              class="mt-12px"
              :page="orderPage"
              :page-size="pageSize"
              :item-count="orderTotal"
              @update:page="page => project && selectProject(project, page)"
            />
          </NCard>

          <NCard v-if="order" :title="`${order.orderNo} · ${t('tickets')}`" size="small">
            <template #header-extra>
              <NButton v-if="canEditTickets" type="primary" size="small" @click="openTicket()">
                {{ t('addTicket') }}
              </NButton>
            </template>
            <NSpin :show="loadingTickets">
              <NEmpty v-if="!tickets.length" :description="t('emptyTickets')" />
              <NSpace v-else vertical :size="12">
                <NCard v-for="item in tickets" :key="item.id" embedded size="small">
                  <template #header>
                    <NSpace align="center">
                      <span class="font-mono">{{ item.ticketCode }}</span>
                      <NTag v-if="!item.allocations.length" size="small" type="warning">{{ t('unassigned') }}</NTag>
                    </NSpace>
                  </template>
                  <template #header-extra>
                    <NSpace>
                      <NButton v-if="canEditTickets" size="tiny" secondary @click="openTicket(item)">
                        {{ $t('common.edit') }}
                      </NButton>
                      <NButton v-if="canAllocate" size="tiny" type="primary" secondary @click="openAllocation(item)">
                        {{ t('allocate') }}
                      </NButton>
                    </NSpace>
                  </template>
                  <NSpace class="mb-8px" align="center">
                    <span>{{ t('totalHours') }} {{ item.totalHours ?? '—' }}</span>
                    <span>{{ t('assignedHours') }} {{ item.assignedHours }}</span>
                    <span v-if="item.totalHours !== null">
                      {{ t('remainingHours') }} {{ (Number(item.totalHours) - Number(item.assignedHours)).toFixed(2) }}
                    </span>
                  </NSpace>
                  <NTable v-if="item.allocations.length" size="small">
                    <thead>
                      <tr>
                        <th>{{ t('worker') }}</th>
                        <th>{{ t('assignedOn') }}</th>
                        <th>{{ t('hours') }}</th>
                        <th v-if="canAllocate">{{ $t('common.action') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="record in item.allocations" :key="record.id">
                        <td>{{ record.workerName }}</td>
                        <td>{{ record.assignedOn }}</td>
                        <td>{{ record.hours ?? '—' }}</td>
                        <td v-if="canAllocate">
                          <NButton size="tiny" text @click="openAllocation(item, record)">
                            {{ $t('common.edit') }}
                          </NButton>
                        </td>
                      </tr>
                    </tbody>
                  </NTable>
                </NCard>
              </NSpace>
            </NSpin>
          </NCard>
        </NSpace>
      </div>
    </NTabPane>

    <NTabPane name="report" :tab="t('report')">
      <AssetReport />
    </NTabPane>
  </NTabs>

  <ExcelImportPreview
    v-if="importFile"
    :file="importFile"
    :preview-api="fetchPreviewImportWorkProject"
    :import-api="importProjects"
    @close="importFile = null"
  />

  <NModal
    v-model:show="ticketVisible"
    preset="card"
    class="max-w-640px w-95vw"
    :title="editingTicket ? t('editTicket') : t('addTicket')"
    :mask-closable="!ticketBusy"
    :close-on-esc="!ticketBusy"
  >
    <NForm>
      <NFormItem :label="t('ticketCode')">
        <NInput
          v-model:value="ticketForm.ticketCode"
          :maxlength="100"
          :placeholder="t('ticketCodePlaceholder')"
          @update:value="ticketForm.codeSource = 'manual'"
        />
      </NFormItem>
      <NFormItem :label="t('totalHours')">
        <NInputNumber v-model:value="ticketForm.totalHours" :min="0" :max="99999.99" :precision="2" clearable />
      </NFormItem>
      <NButton v-if="canUseOcr" secondary @click="showOcr = !showOcr">{{ t('ocr') }}</NButton>
      <NSpace v-if="showOcr" vertical class="mt-12px">
        <OcrRecognizer @recognized="ocrRecognized" />
        <NSelect
          v-if="ocrOptions.length"
          :options="ocrOptions"
          :placeholder="t('chooseOcr')"
          @update:value="
            code => {
              ticketForm.ticketCode = code;
              ticketForm.codeSource = 'ocr';
            }
          "
        />
      </NSpace>
    </NForm>
    <template #footer>
      <NButton type="primary" :loading="ticketBusy" :disabled="!ticketForm.ticketCode.trim()" @click="saveTicket">
        {{ t('save') }}
      </NButton>
    </template>
  </NModal>

  <NModal
    :show="Boolean(allocation)"
    preset="card"
    class="max-w-440px w-95vw"
    :title="t('allocate')"
    :mask-closable="!allocationBusy"
    :close-on-esc="!allocationBusy"
    @update:show="value => !value && !allocationBusy && (allocation = null)"
  >
    <NForm>
      <NFormItem :label="t('worker')">
        <NSelect v-model:value="assignedWorker" :options="workerOptions" filterable :placeholder="t('worker')" />
      </NFormItem>
      <NFormItem :label="t('assignedOn')">
        <NDatePicker v-model:formatted-value="assignedOn" type="date" value-format="yyyy-MM-dd" />
      </NFormItem>
      <NFormItem :label="t('hours')">
        <NInputNumber v-model:value="assignedHours" :min="0" :max="99999.99" :precision="2" clearable />
      </NFormItem>
    </NForm>
    <template #footer>
      <NButton
        type="primary"
        :loading="allocationBusy"
        :disabled="!assignedWorker || !assignedOn"
        @click="saveAllocation"
      >
        {{ t('save') }}
      </NButton>
    </template>
  </NModal>
</template>
