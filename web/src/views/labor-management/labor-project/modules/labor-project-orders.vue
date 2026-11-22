<script setup lang="ts">
import { computed, h, onBeforeUnmount, ref, watch } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { $t } from '@/locales';
import LaborOrderWorkHours from './labor-order-work-hours.vue';
import { fetchMatchingOrders } from './matching-orders';

const props = defineProps<{ partNo: string }>();
const orders = ref<Api.OrderManagementManage.Order[]>([]);
const loading = ref(false);
const failed = ref(false);
let requestSequence = 0;

const columns = computed<DataTableColumns<Api.OrderManagementManage.Order>>(() => [
  { type: 'expand', expandable: () => true, renderExpand: row => h(LaborOrderWorkHours, { orderNo: row.orderNo }) },
  { key: 'orderNo', title: $t('page.order_management.order.orderNo'), minWidth: 150 },
  { key: 'name', title: $t('page.order_management.order.name'), minWidth: 150 },
  { key: 'quantity', title: $t('page.order_management.order.quantity'), minWidth: 90 },
  { key: 'receivedQuantity', title: $t('page.order_management.order.receivedQuantity'), minWidth: 100 },
  { key: 'unit', title: $t('page.order_management.order.unit'), minWidth: 80 },
  { key: 'orderDueDate', title: $t('page.order_management.order.orderDueDate'), minWidth: 120 }
]);

async function loadOrders() {
  const current = ++requestSequence;
  const partNo = props.partNo;
  loading.value = true;
  failed.value = false;
  orders.value = [];
  try {
    const matches = await fetchMatchingOrders(partNo, () => current === requestSequence);
    if (matches) orders.value = matches;
  } catch {
    if (current === requestSequence) failed.value = true;
  } finally {
    if (current === requestSequence) loading.value = false;
  }
}

watch(() => props.partNo, loadOrders, { immediate: true });
onBeforeUnmount(() => {
  requestSequence += 1;
});
</script>

<template>
  <div class="px-12px py-8px">
    <NSpin :show="loading">
      <NAlert v-if="failed" type="error">
        {{ $t('page.labor_management.labor_project.ordersLoadFailed') }}
        <NButton text type="primary" class="ml-8px" @click="loadOrders">
          {{ $t('page.labor_management.labor_project.retryOrders') }}
        </NButton>
      </NAlert>
      <NEmpty
        v-else-if="!loading && !orders.length"
        :description="$t('page.labor_management.labor_project.noMatchedOrders')"
      />
      <template v-else-if="orders.length">
        <div class="mb-8px font-medium">
          {{ $t('page.labor_management.labor_project.matchedOrders') }} · {{ orders.length }}
        </div>
        <NDataTable
          :columns="columns"
          :data="orders"
          :row-key="row => row.id"
          :pagination="{ pageSize: 10 }"
          :scroll-x="1000"
          size="small"
        />
      </template>
    </NSpin>
  </div>
</template>
