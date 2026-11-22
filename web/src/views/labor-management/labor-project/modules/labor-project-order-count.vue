<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import { $t } from '@/locales';
import { fetchMatchingOrders } from './matching-orders';

const props = defineProps<{ partNo: string }>();
const count = ref<number | null>(null);
const failed = ref(false);
const loading = ref(false);
let sequence = 0;

async function load() {
  const current = ++sequence;
  count.value = null;
  failed.value = false;
  loading.value = true;
  try {
    const orders = await fetchMatchingOrders(props.partNo, () => current === sequence);
    if (orders) count.value = orders.length;
  } catch {
    if (current === sequence) failed.value = true;
  } finally {
    if (current === sequence) loading.value = false;
  }
}

watch(() => props.partNo, load, { immediate: true });
onBeforeUnmount(() => {
  sequence += 1;
});
</script>

<template>
  <NSpin v-if="loading" size="small" />
  <NButton v-else-if="failed" text type="error" @click="load">
    {{ $t('page.labor_management.labor_project.retryOrders') }}
  </NButton>
  <span v-else>{{ count ?? '—' }}</span>
</template>
