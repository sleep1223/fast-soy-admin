<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

const booleanOptions = [
  { label: $t('common.yesOrNo.yes'), value: true },
  { label: $t('common.yesOrNo.no'), value: false }
] as any;

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  rateOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  rateOptions: () => []
});

defineOptions({ name: 'WeighingTicketSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WeighbridgeSettlementManage.WeighingTicketSearchParams>('model', { required: true });
const weighingDateRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.weighingDateStart && model.value.weighingDateEnd
      ? [model.value.weighingDateStart, model.value.weighingDateEnd]
      : null,
  set: (value: [string, string] | null) => {
    model.value.weighingDateStart = value?.[0] ?? null;
    model.value.weighingDateEnd = value?.[1] ?? null;
  }
});

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['weighing-ticket-search']">
      <NCollapseItem :title="$t('common.search')" name="weighing-ticket-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.weighing_ticket.weighingDate')"
              path="weighingDate"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="weighingDateRange"
                type="daterange"
                value-format="yyyy-MM-dd"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.weighing_ticket.ticketNo')"
              path="ticketNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.ticketNo"
                :placeholder="$t('page.weighbridge_settlement.weighing_ticket.form.ticketNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.weighing_ticket.process')"
              path="process"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.process"
                :placeholder="$t('page.weighbridge_settlement.weighing_ticket.form.process')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.weighing_ticket.isSettled')"
              path="isSettled"
              class="pr-24px"
            >
              <NSelect
                :value="model.isSettled as any"
                :options="booleanOptions"
                clearable
                :placeholder="$t('page.weighbridge_settlement.weighing_ticket.form.isSettled')"
                @update:value="value => (model.isSettled = value as boolean | null)"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.weighing_ticket.rate')"
              path="rateId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.rateId"
                :options="props.rateOptions"
                clearable
                filterable
                :placeholder="$t('page.weighbridge_settlement.weighing_ticket.form.rate')"
              />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6">
              <NSpace class="w-full" justify="end">
                <NButton @click="reset">
                  <template #icon><icon-ic-round-refresh class="text-icon" /></template>
                  {{ $t('common.reset') }}
                </NButton>
                <NButton type="primary" attr-type="submit" ghost>
                  <template #icon><icon-ic-round-search class="text-icon" /></template>
                  {{ $t('common.search') }}
                </NButton>
              </NSpace>
            </NFormItemGi>
          </NGrid>
        </NForm>
      </NCollapseItem>
    </NCollapse>
  </NCard>
</template>
