<script setup lang="ts">
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  orderOptions?: SelectOptionItem[];
  productionUnitOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  orderOptions: () => [],
  productionUnitOptions: () => []
});

defineOptions({ name: 'OrderUnitMappingSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.OrderUnitMappingSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['order-unit-mapping-search']">
      <NCollapseItem :title="$t('common.search')" name="order-unit-mapping-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.order_unit_mapping.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.order_unit_mapping.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.order_unit_mapping.order')"
              path="orderId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.orderId"
                :options="props.orderOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.order_unit_mapping.form.order')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.order_unit_mapping.productionUnit')"
              path="productionUnitId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.productionUnitId"
                :options="props.productionUnitOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.order_unit_mapping.form.productionUnit')"
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
