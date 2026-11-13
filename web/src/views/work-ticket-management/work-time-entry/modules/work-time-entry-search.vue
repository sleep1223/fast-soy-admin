<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  assignmentOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  assignmentOptions: () => []
});

defineOptions({ name: 'WorkTimeEntrySearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.WorkTimeEntrySearchParams>('model', { required: true });
const workDateRange = computed<[string, string] | null>({
  get: (): [string, string] | null =>
    model.value.workDateStart && model.value.workDateEnd ? [model.value.workDateStart, model.value.workDateEnd] : null,
  set: (value: [string, string] | null) => {
    model.value.workDateStart = value?.[0] ?? null;
    model.value.workDateEnd = value?.[1] ?? null;
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
    <NCollapse :default-expanded-names="['work-time-entry-search']">
      <NCollapseItem :title="$t('common.search')" name="work-time-entry-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_time_entry.workDate')"
              path="workDate"
              class="pr-24px"
            >
              <NDatePicker
                v-model:formatted-value="workDateRange"
                type="daterange"
                value-format="yyyy-MM-dd"
                clearable
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_time_entry.accountingMonth')"
              path="accountingMonth"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.accountingMonth"
                :placeholder="$t('page.work_ticket_management.work_time_entry.form.accountingMonth')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_time_entry.hours')"
              path="hours"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.hours"
                :placeholder="$t('page.work_ticket_management.work_time_entry.form.hours')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_time_entry.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.work_time_entry.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_time_entry.assignment')"
              path="assignmentId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.assignmentId"
                :options="props.assignmentOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_time_entry.form.assignment')"
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
