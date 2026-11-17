<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import ImagePreview from '@/components/advanced/image-preview.vue';
import ImageUpload from '@/components/advanced/image-upload.vue';
import {
  fetchAddWeighingTicket,
  fetchGetWeighingTicket,
  fetchSettlementPreview,
  fetchSettlementRateOptions,
  fetchUpdateWeighingTicket
} from '@/service/api';
import { $t } from '@/locales';
import WeighingLineEditor from './weighing-line-editor.vue';
import WeighingLineTable from './weighing-line-table.vue';

defineOptions({ name: 'WeighingTicketOperateDrawer' });
const props = defineProps<{
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WeighbridgeSettlementManage.WeighingTicket | null;
  readonly?: boolean;
}>();
const emit = defineEmits<{ submitted: [] }>();
const visible = defineModel<boolean>('visible', { default: false });
const loading = ref(false);
const failed = ref(false);
const saving = ref(false);
const uploading = ref(false);
const rates = ref<Api.WeighbridgeSettlementManage.RateOption[]>([]);
const model = ref(defaultModel());
// NDatePicker requires null for an empty date; an empty string parses to NaN.
const weighingDate = computed({
  get: () => model.value.weighingDate || null,
  set: (value: string | null) => {
    model.value.weighingDate = value ?? '';
  }
});
const process = ref('');
const price = ref('');
const revision = ref(1);
const settled = ref(false);
const rateChanged = ref(false);
const preview = ref<Api.WeighbridgeSettlementManage.Preview | null>(null);
const previewLoading = ref(false);
const previewError = ref(false);
const readonly = computed(() => Boolean(props.readonly || settled.value));
const title = computed(() =>
  readonly.value
    ? $t('page.weighbridge_settlement.settlement.details')
    : $t(
        props.operateType === 'add'
          ? 'page.weighbridge_settlement.weighing_ticket.addWeighingTicket'
          : 'page.weighbridge_settlement.weighing_ticket.editWeighingTicket'
      )
);
let session = 0;
let previewSequence = 0;
let timer: ReturnType<typeof setTimeout> | undefined;
let draftKey: string | null = null;
let draftReady = false;
let nextKey = 0;
const rowKeys = ref<number[]>([]);
function defaultModel(): Api.WeighbridgeSettlementManage.WeighingTicketAddParams {
  return { ticketNo: '', weighingDate: '', weight: '', rateId: undefined, images: [], lines: [] };
}
function toInput(line: Api.WeighbridgeSettlementManage.LineInput): Api.WeighbridgeSettlementManage.LineInput {
  return {
    id: line.id,
    orderId: line.orderId,
    orderNo: line.orderNo,
    partNo: line.partNo,
    name: line.name,
    netWeight: line.netWeight?.trim() || null,
    grossWeight: line.grossWeight?.trim() || null,
    quantity: line.quantity
  };
}
const rateOptions = computed(() => {
  const result: { label: string; value: string; disabled?: boolean }[] = rates.value.map(rate => ({
    label: `${rate.processName} (${rate.price})`,
    value: rate.id
  }));
  if (model.value.rateId && !result.some(option => option.value === model.value.rateId))
    result.push({ label: process.value, value: model.value.rateId, disabled: true });
  return result;
});
function selectRate(id: string) {
  const rate = rates.value.find(item => item.id === id);
  if (!rate) return;
  model.value.rateId = id;
  process.value = rate.processName;
  price.value = rate.price;
  rateChanged.value = true;
}
function addLine() {
  model.value.lines.push({ orderId: null, orderNo: '', partNo: '', name: '', netWeight: '', quantity: 0 });
  rowKeys.value.push(++nextKey);
}
function removeLine(index: number) {
  model.value.lines.splice(index, 1);
  rowKeys.value.splice(index, 1);
}
function validOptionalWeight(value: string | null | undefined) {
  const weight = value?.trim() ?? '';
  return !weight || (/^\d+(\.\d{1,6})?$/.test(weight) && Number(weight) > 0);
}
function valid() {
  return (
    /^\d+(\.\d{1,3})?$/.test(model.value.weight) &&
    Number(model.value.weight) > 0 &&
    Number(price.value) > 0 &&
    model.value.lines.length > 0 &&
    model.value.lines.every(
      line =>
        line.partNo.trim() &&
        line.name.trim() &&
        validOptionalWeight(line.netWeight) &&
        /^\d+(\.\d{1,6})?$/.test(line.grossWeight ?? '') &&
        Number(line.grossWeight) > 0 &&
        Number.isInteger(line.quantity) &&
        line.quantity > 0
    )
  );
}
async function runPreview(current: number) {
  const { data, error } = await fetchSettlementPreview({
    weight: model.value.weight,
    price: price.value,
    lines: model.value.lines.map(toInput)
  });
  if (current !== previewSequence || !visible.value) return;
  previewLoading.value = false;
  previewError.value = Boolean(error);
  preview.value = error ? null : data;
}
watch(
  [() => model.value.weight, () => model.value.lines, price],
  () => {
    clearTimeout(timer);
    const current = ++previewSequence;
    if (!visible.value || loading.value || readonly.value) return;
    preview.value = null;
    previewError.value = false;
    previewLoading.value = valid();
    if (previewLoading.value) timer = setTimeout(() => runPreview(current), 300);
  },
  { deep: true }
);
async function initialize() {
  const current = ++session;
  loading.value = true;
  failed.value = false;
  uploading.value = false;
  model.value = defaultModel();
  preview.value = null;
  process.value = '';
  price.value = '';
  settled.value = false;
  rateChanged.value = false;
  const [options, ticket] = await Promise.all([
    fetchSettlementRateOptions(),
    props.operateType === 'edit' && props.rowData ? fetchGetWeighingTicket(props.rowData.id) : Promise.resolve(null)
  ]);
  if (session !== current || !visible.value) return;
  rates.value = options.data ?? [];
  failed.value = Boolean(options.error || ticket?.error);
  if (ticket?.data) {
    const data = ticket.data;
    model.value = {
      ticketNo: data.ticketNo,
      weighingDate: data.weighingDate,
      weight: String(data.weight),
      rateId: data.rateId,
      images: [...(data.images ?? [])],
      lines: data.lines.map(toInput)
    };
    process.value = data.process;
    price.value = String(data.price);
    revision.value = data.revision;
    settled.value = Boolean(data.isSettled);
    preview.value = { totalAmount: data.totalAmount, lines: data.lines };
    rowKeys.value = data.lines.map(() => ++nextKey);
  } else rowKeys.value = [];
  loading.value = false;
  draftReady = true;
}
async function submit() {
  if (uploading.value) return;
  if (
    saving.value ||
    readonly.value ||
    !valid() ||
    !model.value.ticketNo.trim() ||
    !model.value.weighingDate ||
    !model.value.rateId
  ) {
    window.$message?.warning($t('page.weighbridge_settlement.settlement.requiredLines'));
    return;
  }
  saving.value = true;
  try {
    const payload = { ...model.value, lines: model.value.lines.map(toInput) };
    const result =
      props.operateType === 'add'
        ? await fetchAddWeighingTicket(payload)
        : await fetchUpdateWeighingTicket({
            ...payload,
            rateId: rateChanged.value ? payload.rateId : undefined,
            id: props.rowData?.id,
            revision: revision.value
          });
    if (result.error || !result.data) return;
    const saved = await fetchGetWeighingTicket(result.data.id);
    if (saved.error) return;
    window.$message?.success($t('common.updateSuccess'));
    draftKey = null;
    draftReady = false;
    visible.value = false;
    emit('submitted');
  } finally {
    saving.value = false;
  }
}
watch(visible, value => {
  if (value) {
    const key = `${props.operateType}:${props.rowData?.id ?? 'new'}`;
    if (draftKey !== key || !draftReady) {
      draftKey = key;
      draftReady = false;
      initialize();
    }
  } else {
    session++;
    previewSequence++;
    clearTimeout(timer);
  }
});
onBeforeUnmount(() => {
  session++;
  previewSequence++;
  clearTimeout(timer);
});
const previewFields = ['theoreticalWeight', 'allocatedWeight', 'amount', 'taxUnitPrice'] as const;
const totalTheoretical = computed(() => {
  // Display only: exact six-place addition with BigInt, never binary floating point.
  const total = (preview.value?.lines ?? []).reduce((sum, line) => {
    const [whole, fraction = ''] = line.theoreticalWeight.split('.');
    return sum + BigInt(whole) * 1000000n + BigInt(fraction.padEnd(6, '0'));
  }, 0n);
  return `${total / 1000000n}.${String(total % 1000000n).padStart(6, '0')}`;
});
</script>

<template>
  <NDrawer v-model:show="visible" width="min(1100px, 100vw)" :close-on-esc="!saving" :mask-closable="!saving">
    <NDrawerContent :title="title" :closable="!saving">
      <NSpin :show="loading">
        <NAlert v-if="failed" type="error">{{ $t('page.weighbridge_settlement.settlement.loadFailed') }}</NAlert>
        <NForm v-else :disabled="readonly || saving || loading" label-placement="top">
          <div class="grid grid-cols-2 gap-x-16px lt-sm:grid-cols-1">
            <NFormItem :label="$t('page.weighbridge_settlement.weighing_ticket.ticketNo')" required>
              <NInput v-model:value="model.ticketNo" :maxlength="100" />
            </NFormItem>
            <NFormItem :label="$t('page.weighbridge_settlement.weighing_ticket.weighingDate')" required>
              <NDatePicker
                v-model:formatted-value="weighingDate"
                type="date"
                value-format="yyyy-MM-dd"
                class="w-full"
              />
            </NFormItem>
            <NFormItem :label="$t('page.weighbridge_settlement.weighing_ticket.weight')" required>
              <NInput v-model:value="model.weight" placeholder="0.000" />
            </NFormItem>
            <NFormItem :label="$t('page.weighbridge_settlement.weighing_ticket.rate')" required>
              <NSelect :value="model.rateId" :options="rateOptions" filterable @update:value="selectRate" />
            </NFormItem>
          </div>
          <NFormItem :label="$t('page.weighbridge_settlement.weighing_ticket.images')">
            <ImagePreview v-if="readonly" :value="model.images" :width="96" :height="96" />
            <ImageUpload
              v-else-if="visible && !loading"
              v-model:value="model.images"
              v-model:busy="uploading"
              value-type="array"
              :limit="5"
              :disabled="saving"
            />
          </NFormItem>
          <NSpace vertical class="mb-16px">
            <NText>
              {{ process }} · {{ $t('page.weighbridge_settlement.weighing_ticket.price') }}: {{ price || '—' }}
            </NText>
            <NText>
              {{ $t('page.weighbridge_settlement.weighing_ticket.isSettled') }}:
              {{
                settled
                  ? $t('page.weighbridge_settlement.settlement.settled')
                  : $t('page.weighbridge_settlement.settlement.unsettled')
              }}
            </NText>
            <NButton v-if="!readonly && model.rateId" size="small" @click="selectRate(model.rateId)">
              {{ $t('page.weighbridge_settlement.settlement.refreshPrice') }}
            </NButton>
          </NSpace>
          <NDivider>{{ $t('page.weighbridge_settlement.settlement.lines') }}</NDivider>
          <WeighingLineTable v-if="readonly" :lines="preview?.lines ?? []" />
          <template v-else>
            <NCard v-for="(line, index) in model.lines" :key="rowKeys[index]" size="small" class="mb-12px">
              <template #header>
                <NSpace align="center" :size="8">
                  <NTag round size="small" type="info">{{ index + 1 }}</NTag>
                  <NText strong>{{ line.partNo || $t('page.weighbridge_settlement.settlement.partNo') }}</NText>
                </NSpace>
              </template>
              <template v-if="!readonly" #header-extra>
                <NSpace align="center" :size="8">
                  <NTag :type="line.orderId ? 'success' : 'default'" size="small" :bordered="false">
                    {{
                      line.orderId
                        ? $t('page.weighbridge_settlement.settlement.matched')
                        : $t('page.weighbridge_settlement.settlement.manual')
                    }}
                  </NTag>
                  <NButton size="small" type="error" ghost @click="removeLine(index)">
                    {{ $t('common.delete') }}
                  </NButton>
                </NSpace>
              </template>
              <WeighingLineEditor v-model="model.lines[index]" :readonly="readonly" />
              <div class="mt-12px grid grid-cols-2 gap-x-16px gap-y-8px rounded bg-gray-50 p-12px dark:bg-gray-800">
                <NText v-for="field in previewFields" :key="field">
                  {{ $t(`page.weighbridge_settlement.settlement.${field}`) }}:
                  {{ preview?.lines[index]?.[field] ?? '—' }}
                </NText>
              </div>
            </NCard>
          </template>
          <NButton v-if="!readonly" type="primary" dashed block class="mb-12px" @click="addLine">
            <template #icon><icon-ic-round-add class="text-icon" /></template>
            {{ $t('page.weighbridge_settlement.settlement.addLine') }}
          </NButton>
          <NAlert v-if="previewError" type="error" class="mt-16px">
            {{ $t('page.weighbridge_settlement.settlement.previewFailed') }}
          </NAlert>
          <NSpin :show="previewLoading">
            <NDescriptions
              bordered
              :column="1"
              class="mt-16px"
              :title="$t('page.weighbridge_settlement.settlement.preview')"
            >
              <NDescriptionsItem :label="$t('page.weighbridge_settlement.settlement.totalTheoreticalWeight')">
                {{ preview ? totalTheoretical : '—' }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.weighbridge_settlement.weighing_ticket.weight')">
                {{ model.weight }}
              </NDescriptionsItem>
              <NDescriptionsItem :label="$t('page.weighbridge_settlement.weighing_ticket.totalAmount')">
                {{ preview?.totalAmount ?? '—' }}
              </NDescriptionsItem>
            </NDescriptions>
          </NSpin>
        </NForm>
      </NSpin>
      <template #footer>
        <NSpace>
          <NButton :disabled="saving" @click="visible = false">{{ $t('common.cancel') }}</NButton>
          <NButton
            v-if="!readonly"
            type="primary"
            :loading="saving"
            :disabled="loading || failed || uploading"
            @click="submit"
          >
            {{ $t('common.confirm') }}
          </NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
