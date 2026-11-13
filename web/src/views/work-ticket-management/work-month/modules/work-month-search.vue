<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  statusOptions?: SelectOptionItem[];
  productionUnitOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  statusOptions: () => [],
  productionUnitOptions: () => []
});

defineOptions({ name: 'WorkMonthSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.WorkMonthSearchParams>('model', { required: true });
const closedAtRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.closedAtStart && model.value.closedAtEnd ? [model.value.closedAtStart, model.value.closedAtEnd] : null,
  set: (value: [string, string] | null) => {
    model.value.closedAtStart = value?.[0] ?? null;
    model.value.closedAtEnd = value?.[1] ?? null;
  }
});
const reopenedAtRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.reopenedAtStart && model.value.reopenedAtEnd
      ? [model.value.reopenedAtStart, model.value.reopenedAtEnd]
      : null,
  set: (value: [string, string] | null) => {
    model.value.reopenedAtStart = value?.[0] ?? null;
    model.value.reopenedAtEnd = value?.[1] ?? null;
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
    <NCollapse :default-expanded-names="['work-month-search']">
      <NCollapseItem :title="$t('common.search')" name="work-month-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.yearMonth')"
              path="yearMonth"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.yearMonth"
                :placeholder="$t('page.work_ticket_management.work_month.form.yearMonth')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.status')"
              path="status"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.status"
                :options="props.statusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_month.form.status')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.work_month.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.revision')"
              path="revision"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.revision"
                :placeholder="$t('page.work_ticket_management.work_month.form.revision')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.closedAt')"
              path="closedAt"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="closedAtRange"
                type="datetimerange"
                value-format="yyyy-MM-dd HH:mm:ss"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.closedBy')"
              path="closedBy"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.closedBy"
                :placeholder="$t('page.work_ticket_management.work_month.form.closedBy')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.reopenedAt')"
              path="reopenedAt"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="reopenedAtRange"
                type="datetimerange"
                value-format="yyyy-MM-dd HH:mm:ss"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.reopenCount')"
              path="reopenCount"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.reopenCount"
                :placeholder="$t('page.work_ticket_management.work_month.form.reopenCount')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month.productionUnit')"
              path="productionUnitId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.productionUnitId"
                :options="props.productionUnitOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_month.form.productionUnit')"
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
