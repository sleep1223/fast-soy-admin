<script setup lang="ts">
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  sourceOptions?: SelectOptionItem[];
  ticketOptions?: SelectOptionItem[];
  workerOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  sourceOptions: () => [],
  ticketOptions: () => [],
  workerOptions: () => []
});

defineOptions({ name: 'WorkTicketAssignmentSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.WorkTicketAssignmentSearchParams>('model', { required: true });

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['work-ticket-assignment-search']">
      <NCollapseItem :title="$t('common.search')" name="work-ticket-assignment-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket_assignment.source')"
              path="source"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.source"
                :options="props.sourceOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.source')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket_assignment.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket_assignment.ticket')"
              path="ticketId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.ticketId"
                :options="props.ticketOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.ticket')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket_assignment.worker')"
              path="workerId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.workerId"
                :options="props.workerOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.worker')"
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
