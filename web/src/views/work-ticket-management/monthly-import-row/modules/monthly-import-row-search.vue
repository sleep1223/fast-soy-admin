<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  matchStatusOptions?: SelectOptionItem[];
  matchSourceOptions?: SelectOptionItem[];
  handlingStatusOptions?: SelectOptionItem[];
  batchOptions?: SelectOptionItem[];
  orderOptions?: SelectOptionItem[];
  duplicateOfRowOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  matchStatusOptions: () => [],
  matchSourceOptions: () => [],
  handlingStatusOptions: () => [],
  batchOptions: () => [],
  orderOptions: () => [],
  duplicateOfRowOptions: () => []
});

defineOptions({ name: 'MonthlyImportRowSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.MonthlyImportRowSearchParams>('model', { required: true });
const handledAtRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.handledAtStart && model.value.handledAtEnd
      ? [model.value.handledAtStart, model.value.handledAtEnd]
      : null,
  set: (value: [string, string] | null) => {
    model.value.handledAtStart = value?.[0] ?? null;
    model.value.handledAtEnd = value?.[1] ?? null;
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
    <NCollapse :default-expanded-names="['monthly-import-row-search']">
      <NCollapseItem :title="$t('common.search')" name="monthly-import-row-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.rowNumber')"
              path="rowNumber"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.rowNumber"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.rowNumber')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.rawPartNo')"
              path="rawPartNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.rawPartNo"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.rawPartNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.normalizedPartNo')"
              path="normalizedPartNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.normalizedPartNo"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.normalizedPartNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.matchStatus')"
              path="matchStatus"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.matchStatus"
                :options="props.matchStatusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.matchStatus')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.matchSource')"
              path="matchSource"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.matchSource"
                :options="props.matchSourceOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.matchSource')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.sourceQuantity')"
              path="sourceQuantity"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.sourceQuantity"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.sourceQuantity')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.handlingStatus')"
              path="handlingStatus"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.handlingStatus"
                :options="props.handlingStatusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.handlingStatus')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.handlingNote')"
              path="handlingNote"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.handlingNote"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.handlingNote')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.handledAt')"
              path="handledAt"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="handledAtRange"
                type="datetimerange"
                value-format="yyyy-MM-dd HH:mm:ss"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.handledBy')"
              path="handledBy"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.handledBy"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.handledBy')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.note')"
              path="note"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.note"
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.note')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.batch')"
              path="batchId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.batchId"
                :options="props.batchOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.batch')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.order')"
              path="orderId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.orderId"
                :options="props.orderOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.order')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.monthly_import_row.duplicateOfRow')"
              path="duplicateOfRowId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.duplicateOfRowId"
                :options="props.duplicateOfRowOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.monthly_import_row.form.duplicateOfRow')"
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
