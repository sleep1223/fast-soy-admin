<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  codeSourceOptions?: SelectOptionItem[];
  statusOptions?: SelectOptionItem[];
  reconcileStatusOptions?: SelectOptionItem[];
  workMonthOptions?: SelectOptionItem[];
  orderOptions?: SelectOptionItem[];
  sourceImportRowOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  codeSourceOptions: () => [],
  statusOptions: () => [],
  reconcileStatusOptions: () => [],
  workMonthOptions: () => [],
  orderOptions: () => [],
  sourceImportRowOptions: () => []
});

defineOptions({ name: 'WorkTicketSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.WorkTicketManagementManage.WorkTicketSearchParams>('model', { required: true });
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
    <NCollapse :default-expanded-names="['work-ticket-search']">
      <NCollapseItem :title="$t('common.search')" name="work-ticket-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.orderNoSnapshot')"
              path="orderNoSnapshot"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.orderNoSnapshot"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.orderNoSnapshot')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.partNoSnapshot')"
              path="partNoSnapshot"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.partNoSnapshot"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.partNoSnapshot')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.nameSnapshot')"
              path="nameSnapshot"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.nameSnapshot"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.nameSnapshot')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.ticketCode')"
              path="ticketCode"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.ticketCode"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.ticketCode')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.ticketCodeKey')"
              path="ticketCodeKey"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.ticketCodeKey"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.ticketCodeKey')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.codeSource')"
              path="codeSource"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.codeSource"
                :options="props.codeSourceOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket.form.codeSource')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.codeRuleVersion')"
              path="codeRuleVersion"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.codeRuleVersion"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.codeRuleVersion')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.codeConfidence')"
              path="codeConfidence"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.codeConfidence"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.codeConfidence')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.status')"
              path="status"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.status"
                :options="props.statusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket.form.status')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.reconcileStatus')"
              path="reconcileStatus"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.reconcileStatus"
                :options="props.reconcileStatusOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket.form.reconcileStatus')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.reconcileNote')"
              path="reconcileNote"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.reconcileNote"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.reconcileNote')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.voidReason')"
              path="voidReason"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.voidReason"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.voidReason')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.voidedAt')"
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
              :label="$t('page.work_ticket_management.work_ticket.voidedBy')"
              path="voidedBy"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.voidedBy"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.voidedBy')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.remark')"
              path="remark"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.remark"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.remark')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.revision')"
              path="revision"
              class="pr-24px"
            >
              <NInputNumber
                v-model:value="model.revision"
                :placeholder="$t('page.work_ticket_management.work_ticket.form.revision')"
                class="w-full"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.workMonth')"
              path="workMonthId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.workMonthId"
                :options="props.workMonthOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket.form.workMonth')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.order')"
              path="orderId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.orderId"
                :options="props.orderOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket.form.order')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.work_ticket_management.work_ticket.sourceImportRow')"
              path="sourceImportRowId"
              class="pr-24px"
            >
              <NSelect
                v-model:value="model.sourceImportRowId"
                :options="props.sourceImportRowOptions"
                clearable
                filterable
                :placeholder="$t('page.work_ticket_management.work_ticket.form.sourceImportRow')"
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
