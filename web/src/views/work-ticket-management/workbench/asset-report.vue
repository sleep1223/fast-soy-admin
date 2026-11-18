<script setup lang="ts">
import { onMounted, ref } from 'vue';
import dayjs from 'dayjs';
import { $t } from '@/locales';
import { fetchWorkAssetReport } from '@/service/api/work_ticket_management-assets';
import { fetchProductionUnitOptions } from '@/service/api/work_ticket_management-workflow';

const t = (key: string) => $t(`page.work_ticket_management.assets.${key}` as const);
const today = dayjs();
const range = ref<[string, string] | null>([
  today.startOf('month').format('YYYY-MM-DD'),
  today.endOf('month').format('YYYY-MM-DD')
]);
const productionUnitId = ref<string | null>(null);
const units = ref<{ label: string; value: string }[]>([]);
const rows = ref<NonNullable<Awaited<ReturnType<typeof fetchWorkAssetReport>>['data']>>([]);
const loading = ref(false);

async function search() {
  if (!range.value || loading.value) return;
  loading.value = true;
  const [startDate, endDate] = range.value;
  const { data, error } = await fetchWorkAssetReport({ startDate, endDate, productionUnitId: productionUnitId.value });
  loading.value = false;
  if (!error && data) rows.value = data;
}

onMounted(async () => {
  void search();
  const { data, error } = await fetchProductionUnitOptions();
  if (!error && data) units.value = data.map(item => ({ label: item.name, value: item.id }));
});
</script>

<template>
  <NCard :title="t('report')" size="small">
    <NSpace align="end" class="mb-16px">
      <NFormItem :label="t('assignedOn')" :show-feedback="false">
        <NDatePicker v-model:formatted-value="range" type="daterange" value-format="yyyy-MM-dd" :disabled="loading" />
      </NFormItem>
      <NFormItem :label="t('productionUnit')" :show-feedback="false">
        <NSelect
          v-model:value="productionUnitId"
          class="w-180px"
          :options="units"
          :placeholder="t('allUnits')"
          :disabled="loading"
          clearable
        />
      </NFormItem>
      <NButton type="primary" :disabled="!range" :loading="loading" @click="search">{{ $t('common.search') }}</NButton>
    </NSpace>
    <NSpin :show="loading">
      <NEmpty v-if="!rows.length" :description="t('emptyReport')" />
      <NTable v-else size="small">
        <thead>
          <tr>
            <th>{{ t('worker') }}</th>
            <th>{{ t('productionUnit') }}</th>
            <th>{{ t('allocationCount') }}</th>
            <th>{{ t('assignedHours') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.workerId">
            <td>{{ row.workerName }}</td>
            <td>{{ row.productionUnitName ?? '—' }}</td>
            <td>{{ row.allocationCount }}</td>
            <td>{{ row.hours }}</td>
          </tr>
        </tbody>
      </NTable>
    </NSpin>
  </NCard>
</template>
