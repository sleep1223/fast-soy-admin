<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

const props = defineProps<{ workerId?: string | null; allocationMonth?: string | null }>();
const assigned = computed(() => Boolean(props.workerId && props.allocationMonth));
</script>

<template>
  <NTag :type="assigned ? 'success' : 'warning'" size="small" :bordered="false">
    {{
      $t(
        assigned ? 'page.labor_management.labor_work_hour.assigned' : 'page.labor_management.labor_work_hour.unassigned'
      )
    }}
  </NTag>
</template>
