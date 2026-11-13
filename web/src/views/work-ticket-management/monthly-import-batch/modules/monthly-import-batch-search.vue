<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  sourceTypeOptions?: SelectOptionItem[];
  statusOptions?: SelectOptionItem[];
  workMonthOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  sourceTypeOptions: () => [],
  statusOptions: () => [],
  workMonthOptions: () => []
});

defineOptions({ name: 'MonthlyImportBatchSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.MonthlyImportBatchSearchParams>('model', { required: true });
const voidedAtRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.voidedAtStart && model.value.voidedAtEnd ? [model.value.voidedAtStart, model.value.voidedAtEnd] : null,
  set: (value: [string, string] | null) => {
    model.value.voidedAtStart = value?.[0] ?? null;
    model.value.voidedAtEnd = value?.[1] ?? null;
  }
});

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['monthly-import-batch-search']">
      <NCollapseItem :title="$t('common.search')" name="monthly-import-batch-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.sourceType')"
              path="sourceType"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.sourceType"
                :options="props.sourceTypeOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.sourceType')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.status')"
              path="status"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.status"
                :options="props.statusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.status')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.sourceName')"
              path="sourceName"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.sourceName"
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.sourceName')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.contentHash')"
              path="contentHash"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.contentHash"
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.contentHash')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.rowCount')"
              path="rowCount"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.rowCount"
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.rowCount')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.voidReason')"
              path="voidReason"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.voidReason"
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.voidReason')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.voidedAt')"
              path="voidedAt"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="voidedAtRange"
                type="datetimerange"
                value-format="yyyy-MM-dd HH:mm:ss"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.voidedBy')"
              path="voidedBy"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.voidedBy"
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.voidedBy')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_batch.workMonth')"
              path="workMonthId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.workMonthId"
                :options="props.workMonthOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.workMonth')"
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
