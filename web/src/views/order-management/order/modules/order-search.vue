<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

defineOptions({ name: 'OrderSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.OrderManagementManage.OrderSearchParams>('model', { required: true });

const orderDueDateRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.orderDueDateStart && model.value.orderDueDateEnd
      ? [model.value.orderDueDateStart, model.value.orderDueDateEnd]
      : null,
  set: (value: [string, string] | null) => {
    model.value.orderDueDateStart = value?.[0] ?? null;
    model.value.orderDueDateEnd = value?.[1] ?? null;
  }
});

const completedDateRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.completedDateStart && model.value.completedDateEnd
      ? [model.value.completedDateStart, model.value.completedDateEnd]
      : null,
  set: (value: [string, string] | null) => {
    model.value.completedDateStart = value?.[0] ?? null;
    model.value.completedDateEnd = value?.[1] ?? null;
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
    <NCollapse :default-expanded-names="['order-search']">
      <NCollapseItem :title="$t('common.search')" name="order-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.order_management.order.orderNo')"
              path="orderNo"
              class="pr-24px"
            >
              <NInput v-model:value="model.orderNo" :placeholder="$t('page.order_management.order.form.orderNo')" />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.order_management.order.partNo')"
              path="partNo"
              class="pr-24px"
            >
              <NInput v-model:value="model.partNo" :placeholder="$t('page.order_management.order.form.partNo')" />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6" :label="$t('page.order_management.order.name')" path="name" class="pr-24px">
              <NInput v-model:value="model.name" :placeholder="$t('page.order_management.order.form.name')" />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6" :label="$t('page.order_management.order.unit')" path="unit" class="pr-24px">
              <NInput v-model:value="model.unit" :placeholder="$t('page.order_management.order.form.unit')" />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.order_management.order.orderDueDate')"
              path="orderDueDate"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="orderDueDateRange"
                type="daterange"
                value-format="yyyy-MM-dd"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.order_management.order.completedDate')"
              path="completedDate"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="completedDateRange"
                type="daterange"
                value-format="yyyy-MM-dd"
                clearable
                class="w-full"
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
