<script setup lang="ts">
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  workerOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  workerOptions: () => []
});

defineOptions({ name: 'LaborWorkHourSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.LaborManagementManage.LaborWorkHourSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['labor-work-hour-search']">
      <NCollapseItem :title="$t('common.search')" name="labor-work-hour-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_work_hour.ticketCode')"
              path="ticketCode"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.ticketCode"
                :placeholder="$t('page.labor_management.labor_work_hour.form.ticketCode')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_work_hour.orderNo')"
              path="orderNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.orderNo"
                :placeholder="$t('page.labor_management.labor_work_hour.form.orderNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_work_hour.worker')"
              path="workerId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.workerId"
                :options="props.workerOptions"
                clearable
                filterable
                :placeholder="$t('page.labor_management.labor_work_hour.form.worker')"
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
