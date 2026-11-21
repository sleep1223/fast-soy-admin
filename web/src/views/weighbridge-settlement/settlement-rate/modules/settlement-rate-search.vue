<script setup lang="ts">
import { $t } from '@/locales';

const booleanOptions = [
  { label: $t('common.yesOrNo.yes'), value: true },
  { label: $t('common.yesOrNo.no'), value: false }
] as any;

defineOptions({ name: 'SettlementRateSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WeighbridgeSettlementManage.SettlementRateSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['settlement-rate-search']">
      <NCollapseItem :title="$t('common.search')" name="settlement-rate-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.settlement_rate.processName')"
              path="processName"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.processName"
                :placeholder="$t('page.weighbridge_settlement.settlement_rate.form.processName')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.weighbridge_settlement.settlement_rate.enabled')"
              path="enabled"
              class="pr-24px"
            >
              <NSelect
                :value="model.enabled as any"
                :options="booleanOptions"
                clearable
                :placeholder="$t('page.weighbridge_settlement.settlement_rate.form.enabled')"
                @update:value="value => (model.enabled = value as boolean | null)"
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
