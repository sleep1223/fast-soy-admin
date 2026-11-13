<script setup lang="ts">
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  fromStatusOptions?: SelectOptionItem[];
  toStatusOptions?: SelectOptionItem[];
  actionOptions?: SelectOptionItem[];
  workMonthOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  fromStatusOptions: () => [],
  toStatusOptions: () => [],
  actionOptions: () => [],
  workMonthOptions: () => []
});

defineOptions({ name: 'WorkMonthStatusLogSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.WorkMonthStatusLogSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['work-month-status-log-search']">
      <NCollapseItem :title="$t('common.search')" name="work-month-status-log-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month_status_log.fromStatus')"
              path="fromStatus"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.fromStatus"
                :options="props.fromStatusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_month_status_log.form.fromStatus')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month_status_log.toStatus')"
              path="toStatus"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.toStatus"
                :options="props.toStatusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_month_status_log.form.toStatus')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month_status_log.action')"
              path="action"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.action"
                :options="props.actionOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_month_status_log.form.action')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month_status_log.reason')"
              path="reason"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.reason"
                :placeholder="$t('page.work_ticket_management.work_month_status_log.form.reason')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_month_status_log.workMonth')"
              path="workMonthId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.workMonthId"
                :options="props.workMonthOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_month_status_log.form.workMonth')"
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
