<script setup lang="ts">
import { $t } from '@/locales';

defineOptions({ name: 'LaborWorkerSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.LaborManagementManage.LaborWorkerSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['labor-worker-search']">
      <NCollapseItem :title="$t('common.search')" name="labor-worker-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_worker.employeeNo')"
              path="employeeNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.employeeNo"
                :placeholder="$t('page.labor_management.labor_worker.form.employeeNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_worker.trade')"
              path="trade"
              class="pr-24px"
            >
              <NInput v-model:value="model.trade" :placeholder="$t('page.labor_management.labor_worker.form.trade')" />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_worker.name')"
              path="name"
              class="pr-24px"
            >
              <NInput v-model:value="model.name" :placeholder="$t('page.labor_management.labor_worker.form.name')" />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_worker.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.labor_management.labor_worker.form.remark')"
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
