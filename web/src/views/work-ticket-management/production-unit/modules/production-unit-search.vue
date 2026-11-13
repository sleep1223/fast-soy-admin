<script setup lang="ts">
import { $t } from '@/locales';

const booleanOptions = [
  { label: $t('common.yesOrNo.yes'), value: true },
  { label: $t('common.yesOrNo.no'), value: false }
] as any;

defineOptions({ name: 'ProductionUnitSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.ProductionUnitSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['production-unit-search']">
      <NCollapseItem :title="$t('common.search')" name="production-unit-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.production_unit.code')"
              path="code"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.code"
                :placeholder="$t('page.work_ticket_management.production_unit.form.code')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.production_unit.name')"
              path="name"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.name"
                :placeholder="$t('page.work_ticket_management.production_unit.form.name')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.production_unit.enabled')"
              path="enabled"
              class="pr-24px"
            >
              <NSelect
                :value="model.enabled as any"
                :options="booleanOptions"
                clearable
                :placeholder="$t('page.work_ticket_management.production_unit.form.enabled')"
                @update:value="value => (model.enabled = value as boolean | null)"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.production_unit.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.production_unit.form.remark')"
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
