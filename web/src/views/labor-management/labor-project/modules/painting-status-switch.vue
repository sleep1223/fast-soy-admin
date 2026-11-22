<script setup lang="ts">
import { $t } from '@/locales';

withDefaults(defineProps<{ value?: boolean | null; loading: boolean; canEdit: boolean }>(), { value: undefined });
const emit = defineEmits<{ change: [value: boolean] }>();
</script>

<template>
  <NTooltip v-if="typeof value !== 'boolean'" trigger="hover">
    <template #trigger>
      <NTag type="warning" size="small">{{ $t('page.labor_management.labor_project.paintingUnavailable') }}</NTag>
    </template>
    {{ $t('page.labor_management.labor_project.paintingUnavailableHint') }}
  </NTooltip>
  <NSwitch
    v-else
    :value="value === true"
    :loading="loading"
    :disabled="!canEdit"
    @update:value="emit('change', $event)"
  />
</template>
