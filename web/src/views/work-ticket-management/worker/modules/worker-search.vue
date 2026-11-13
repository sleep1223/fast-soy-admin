<script setup lang="ts">
import { $t } from '@/locales';

const booleanOptions = [
  { label: $t('common.yesOrNo.yes'), value: true },
  { label: $t('common.yesOrNo.no'), value: false }
] as any;

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  productionUnitOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  productionUnitOptions: () => []
});

defineOptions({ name: 'WorkerSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.WorkerSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['worker-search']">
      <NCollapseItem :title="$t('common.search')" name="worker-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.worker.workerNo')"
              path="workerNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.workerNo"
                :placeholder="$t('page.work_ticket_management.worker.form.workerNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.worker.name')"
              path="name"
              class="pr-24px"
            >
              <NInput v-model:value="model.name" :placeholder="$t('page.work_ticket_management.worker.form.name')" />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.worker.enabled')"
              path="enabled"
              class="pr-24px"
            >
              <NSelect
                :value="model.enabled as any"
                :options="booleanOptions"
                clearable
                :placeholder="$t('page.work_ticket_management.worker.form.enabled')"
                @update:value="value => (model.enabled = value as boolean | null)"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.worker.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.worker.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.worker.productionUnit')"
              path="productionUnitId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.productionUnitId"
                :options="props.productionUnitOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.worker.form.productionUnit')"
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
