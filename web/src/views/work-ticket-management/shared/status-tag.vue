<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

defineOptions({ name: 'WorkStatusTag' });

const props = defineProps<{
  kind: 'month' | 'match' | 'handling' | 'ticket' | 'reconcile' | 'assignment' | 'time';
  value: string | null | undefined;
}>();

const map: Record<string, { key: string; type: 'default' | 'success' | 'warning' | 'error' | 'info' }> = {
  draft: { key: 'draft', type: 'default' },
  in_progress: { key: 'inProgress', type: 'info' },
  verified: { key: 'verifiedState', type: 'success' },
  closed: { key: 'closedState', type: 'default' },
  matched: { key: 'matched', type: 'success' },
  ambiguous: { key: 'ambiguous', type: 'warning' },
  missing: { key: 'missing', type: 'error' },
  unassigned: { key: 'unassigned', type: 'warning' },
  other_unit: { key: 'otherUnit', type: 'warning' },
  invalid: { key: 'invalid', type: 'error' },
  pending: { key: 'pending', type: 'default' },
  open: { key: 'open', type: 'default' },
  resolved: { key: 'resolved', type: 'success' },
  ignored: { key: 'ignored', type: 'default' },
  active: { key: 'active', type: 'success' },
  void: { key: 'void', type: 'default' },
  checked: { key: 'checked', type: 'success' },
  assigned: { key: 'assigned', type: 'success' },
  logged: { key: 'logged', type: 'success' }
};

const label = computed(() => {
  const item = map[props.value || ''];
  return item ? $t(`page.work_ticket_management.workflow.${item.key}`) : props.value || '—';
});
const type = computed(() => map[props.value || '']?.type ?? 'default');
</script>

<template>
  <NTag :type="type" size="small" :data-kind="props.kind">{{ label }}</NTag>
</template>
