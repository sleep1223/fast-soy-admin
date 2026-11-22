<script setup lang="ts">
import { computed, h, onBeforeUnmount, ref, watch } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { NButton } from 'naive-ui';
import { $t } from '@/locales';
import LaborOrderWorkHours from './labor-order-work-hours.vue';
import { fetchMatchingOrders } from './matching-orders';

const props = withDefaults(defineProps<{ partNo: string; skipPainting?: boolean }>(), { skipPainting: false });
const emit = defineEmits<{ loaded: [orders: Api.OrderManagementManage.Order[]] }>();
const orders = ref<Api.OrderManagementManage.Order[]>([]);
const expandedOrderKeys = ref<(string | number)[]>([]);
const loading = ref(false);
const failed = ref(false);
let requestSequence = 0;

async function copyOrderNo(value: string) {
  try {
    await navigator.clipboard.writeText(value);
    window.$message?.success($t('page.labor_management.labor_project.copied'));
  } catch {
    window.$message?.error($t('page.labor_management.labor_project.copyFailed'));
  }
}

const columns = computed<DataTableColumns<Api.OrderManagementManage.Order>>(() => [
  {
    type: 'expand',
    expandable: () => true,
    renderExpand: row =>
      expandedOrderKeys.value.includes(row.id)
        ? h(LaborOrderWorkHours, { orderNo: row.orderNo, skipPainting: props.skipPainting })
        : null
  },
  {
    key: 'orderNo',
    title: $t('page.order_management.order.orderNo'),
    minWidth: 150,
    render: row =>
      h('div', { class: 'flex-center gap-4px' }, [
        h('span', { class: 'font-medium' }, row.orderNo),
        h(
          NButton,
          {
            quaternary: true,
            size: 'tiny',
            'aria-label': $t('page.labor_management.labor_project.copy'),
            onClick: (event: MouseEvent) => {
              event.stopPropagation();
              void copyOrderNo(row.orderNo);
            }
          },
          { default: () => h('span', { class: 'icon-ic-round-content-copy text-14px', 'aria-hidden': 'true' }) }
        )
      ])
  },
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
  expandedOrderKeys.value = [];
  try {
    const matches = await fetchMatchingOrders(partNo, () => current === requestSequence);
    if (matches) {
      orders.value = matches;
      emit('loaded', matches);
    }
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
  <div class="labor-project-detail">
    <h2 class="labor-project-detail-heading">
      {{ $t('page.labor_management.labor_project.matchedOrders') }}
      <span v-if="orders.length" class="labor-project-detail-count">{{ orders.length }}</span>
    </h2>
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
      <NDataTable
        v-else-if="orders.length"
        v-model:expanded-row-keys="expandedOrderKeys"
        :columns="columns"
        :data="orders"
        :row-key="row => row.id"
        :scroll-x="1000"
        size="small"
      />
    </NSpin>
  </div>
</template>
