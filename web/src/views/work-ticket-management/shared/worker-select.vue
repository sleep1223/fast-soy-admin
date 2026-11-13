<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { fetchWorkerOptions } from '@/service/api';
import { $t } from '@/locales';

defineOptions({ name: 'WorkerSelect' });

const props = withDefaults(
  defineProps<{
    productionUnitId?: string | null;
    includeDisabled?: boolean;
    multiple?: boolean;
    disabled?: boolean;
  }>(),
  { productionUnitId: null, includeDisabled: false, multiple: true, disabled: false }
);
const value = defineModel<string[] | string | null>('value', { default: () => [] });
const workers = ref<Api.WorkTicketManagement.WorkerOption[]>([]);
const loading = ref(false);
let sequence = 0;

const options = computed(() =>
  workers.value.map(worker => ({
    label: `${worker.name}${worker.workerNo ? ` (${worker.workerNo})` : ''}${worker.enabled ? '' : ` · ${$t('page.work_ticket_management.workflow.disabled')}`}`,
    value: worker.id
  }))
);

async function reload() {
  const current = ++sequence;
  loading.value = true;
  const { data, error } = await fetchWorkerOptions(props.productionUnitId, props.includeDisabled);
  if (current !== sequence) return;
  loading.value = false;
  if (!error && data) workers.value = data;
}

watch(() => [props.productionUnitId, props.includeDisabled], reload);
onMounted(reload);
defineExpose({ reload });
</script>

<template>
  <NSelect
    v-model:value="value"
    :options="options"
    :multiple="props.multiple"
    :loading="loading"
    :disabled="props.disabled"
    filterable
    clearable
    :placeholder="$t('page.work_ticket_management.workflow.worker')"
  />
</template>
