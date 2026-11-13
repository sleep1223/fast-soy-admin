<script setup lang="ts">
import { $t } from '@/locales';
import WorkStatusTag from './status-tag.vue';

defineOptions({ name: 'MonthUnitToolbar' });

const props = defineProps<{
  month: string;
  unitId: string | null;
  units: Api.WorkTicketManagement.UnitOption[];
  status?: string | null;
  loading?: boolean;
}>();
const emit = defineEmits<{
  'update:month': [value: string];
  'update:unitId': [value: string | null];
}>();

function updateMonth(value: string | null) {
  if (value) emit('update:month', value);
}
function updateUnit(value: string | null) {
  emit('update:unitId', value);
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NSpace align="center" wrap>
      <NFormItem :label="$t('page.work_ticket_management.workflow.month')" :show-feedback="false">
        <NDatePicker
          :formatted-value="props.month"
          type="month"
          value-format="yyyy-MM"
          :clearable="false"
          :disabled="loading"
          class="w-150px"
          @update:formatted-value="updateMonth"
        />
      </NFormItem>
      <NFormItem :label="$t('page.work_ticket_management.workflow.unit')" :show-feedback="false">
        <NSelect
          :value="props.unitId"
          :options="props.units.map(unit => ({ label: `${unit.name} (${unit.code})`, value: unit.id }))"
          filterable
          clearable
          :disabled="loading"
          class="w-240px"
          @update:value="updateUnit"
        />
      </NFormItem>
      <WorkStatusTag v-if="props.status" kind="month" :value="props.status" />
      <slot />
    </NSpace>
  </NCard>
</template>
