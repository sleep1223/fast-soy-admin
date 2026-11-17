<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import { fetchSettlementOrderOptions } from '@/service/api';
import { $t } from '@/locales';

const line = defineModel<Api.WeighbridgeSettlementManage.LineInput>({ required: true });
defineProps<{ readonly?: boolean }>();
const netWeight = computed({
  get: () => line.value.netWeight ?? '',
  set: (value: string) => {
    line.value.netWeight = value.trim() || null;
  }
});
const manual = ref(!line.value.orderId && Boolean(line.value.partNo));
const missingGrossWeight = ref(!(Number(line.value.grossWeight) > 0));
const query = ref('');
const options = ref<Api.WeighbridgeSettlementManage.OrderOption[]>([]);
const searching = ref(false);
const selectOptions = computed(() => {
  const result = options.value.map(order => ({
    value: order.id,
    label: `${order.partNo} | ${order.orderNo} | ${order.name} | ${order.netWeight ?? '—'} kg`
  }));
  if (line.value.orderId && !result.some(option => option.value === line.value.orderId)) {
    result.push({
      value: line.value.orderId,
      label: `${line.value.partNo} | ${line.value.orderNo ?? ''} | ${line.value.name} | ${line.value.netWeight ?? '—'} kg`
    });
  }
  return result;
});
let timer: ReturnType<typeof setTimeout> | undefined;
let sequence = 0;
function search(value: string) {
  query.value = value.trim();
  clearTimeout(timer);
  const current = ++sequence;
  if (!value.trim()) {
    options.value = [];
    searching.value = false;
    return;
  }
  searching.value = true;
  timer = setTimeout(async () => {
    const { data, error } = await fetchSettlementOrderOptions(value.trim());
    if (current !== sequence) return;
    searching.value = false;
    options.value = error ? [] : (data ?? []);
  }, 300);
}
function choose(id: string) {
  const order = options.value.find(item => item.id === id);
  if (order) {
    missingGrossWeight.value = !(Number(order.grossWeight) > 0);
    Object.assign(line.value, {
      orderId: order.id,
      partNo: order.partNo,
      orderNo: order.orderNo,
      name: order.name,
      netWeight: order.netWeight,
      grossWeight: order.grossWeight ?? null
    });
  }
}
function setManual(value: boolean) {
  manual.value = value;
  if (value) {
    line.value.orderId = null;
    if (!line.value.partNo) line.value.partNo = query.value;
    clearTimeout(timer);
    sequence++;
    searching.value = false;
  }
}
onBeforeUnmount(() => {
  clearTimeout(timer);
  sequence++;
});
</script>

<template>
  <div class="min-w-260px flex flex-col gap-8px">
    <NSpace v-if="!readonly" class="mb-4px">
      <NButton :type="!manual ? 'primary' : 'default'" :secondary="!manual" size="small" @click="setManual(false)">
        {{ $t('page.weighbridge_settlement.settlement.matched') }}
      </NButton>
      <NButton :type="manual ? 'primary' : 'default'" :secondary="manual" size="small" @click="setManual(true)">
        {{ $t('page.weighbridge_settlement.settlement.manual') }}
      </NButton>
    </NSpace>
    <NSelect
      v-if="!manual && !readonly"
      :value="line.orderId"
      remote
      filterable
      :loading="searching"
      :options="selectOptions"
      :placeholder="$t('page.weighbridge_settlement.settlement.searchOrders')"
      @search="search"
      @update:value="choose"
    >
      <template #empty>{{ $t('page.weighbridge_settlement.settlement.noOrders') }}</template>
    </NSelect>
    <NGrid cols="1 s:2" responsive="screen" :x-gap="12" :y-gap="4">
      <NGi>
        <NFormItem :label="$t('page.weighbridge_settlement.settlement.partNo')" :show-feedback="false">
          <NInput v-model:value="line.partNo" :disabled="readonly || !manual" />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem :label="$t('page.weighbridge_settlement.settlement.orderNo')" :show-feedback="false">
          <NInput v-model:value="line.orderNo" :disabled="readonly || !manual" />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem :label="$t('page.weighbridge_settlement.settlement.name')" :show-feedback="false">
          <NInput v-model:value="line.name" :disabled="readonly || !manual" />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem :label="$t('page.weighbridge_settlement.settlement.netWeight')" :show-feedback="false">
          <NInput v-model:value="netWeight" :disabled="readonly || !manual" />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem :label="$t('page.weighbridge_settlement.settlement.grossWeight')" :show-feedback="false">
          <NInput v-model:value="line.grossWeight" :disabled="readonly || (!manual && !missingGrossWeight)" />
        </NFormItem>
      </NGi>
      <NGi>
        <NFormItem :label="$t('page.weighbridge_settlement.settlement.quantity')" :show-feedback="false">
          <NInputNumber
            :value="line.quantity"
            :min="1"
            :max="2147483647"
            :precision="0"
            :disabled="readonly"
            class="w-full"
            @update:value="value => (line.quantity = value ?? 0)"
          />
        </NFormItem>
      </NGi>
    </NGrid>
  </div>
</template>
