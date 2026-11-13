<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddWorkTicket, fetchUpdateWorkTicket } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'WorkTicketOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.WorkTicket | null;
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

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();
const visible = defineModel<boolean>('visible', { default: false });
const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.work_ticket_management.work_ticket.addWorkTicket'),
    edit: $t('page.work_ticket_management.work_ticket.editWorkTicket')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.WorkTicketAddParams {
  return {
    orderNoSnapshot: '',
    partNoSnapshot: '',
    nameSnapshot: '',
    ticketCode: '',
    ticketCodeKey: '',
    codeSource: '',
    codeRuleVersion: '',
    codeConfidence: null,
    status: '',
    reconcileStatus: '',
    reconcileNote: '',
    voidReason: '',
    voidedAt: null,
    voidedBy: '',
    remark: '',
    revision: null,
    workMonthId: null,
    orderId: null,
    sourceImportRowId: null
  } as unknown as Api.WorkTicketManagementManage.WorkTicketAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  workMonthId: defaultRequiredRule
};

function handleInitModel() {
  model.value = createDefaultModel();
  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model.value, jsonClone(props.rowData));
  }
}

function closeDrawer() {
  visible.value = false;
}

async function handleSubmit() {
  await validate();

  if (props.operateType === 'add') {
    const { error } = await fetchAddWorkTicket(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateWorkTicket({ id: props.rowData?.id, ...model.value });
    if (error) return;
    window.$message?.success($t('common.updateSuccess'));
  }
  closeDrawer();
  emit('submitted');
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="420">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model" :rules="rules">
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.orderNoSnapshot')" path="orderNoSnapshot">
          <NInput
            v-model:value="model.orderNoSnapshot"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.orderNoSnapshot')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.partNoSnapshot')" path="partNoSnapshot">
          <NInput
            v-model:value="model.partNoSnapshot"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.partNoSnapshot')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.nameSnapshot')" path="nameSnapshot">
          <NInput
            v-model:value="model.nameSnapshot"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.nameSnapshot')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.ticketCode')" path="ticketCode">
          <NInput
            v-model:value="model.ticketCode"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.ticketCode')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.ticketCodeKey')" path="ticketCodeKey">
          <NInput
            v-model:value="model.ticketCodeKey"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.ticketCodeKey')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.codeSource')" path="codeSource">
          <NSelect
            v-model:value="model.codeSource"
            :options="props.codeSourceOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket.form.codeSource')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.codeRuleVersion')" path="codeRuleVersion">
          <NInput
            v-model:value="model.codeRuleVersion"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.codeRuleVersion')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.codeConfidence')" path="codeConfidence">
          <NInputNumber
            v-model:value="model.codeConfidence"
            :precision="2"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.codeConfidence')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.status')" path="status">
          <NSelect
            v-model:value="model.status"
            :options="props.statusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket.form.status')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.reconcileStatus')" path="reconcileStatus">
          <NSelect
            v-model:value="model.reconcileStatus"
            :options="props.reconcileStatusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket.form.reconcileStatus')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.reconcileNote')" path="reconcileNote">
          <NInput
            v-model:value="model.reconcileNote"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.reconcileNote')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.voidReason')" path="voidReason">
          <NInput
            v-model:value="model.voidReason"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.voidReason')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.voidedAt')" path="voidedAt">
          <NDatePicker
            v-model:formatted-value="model.voidedAt"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.voidedBy')" path="voidedBy">
          <NInput
            v-model:value="model.voidedBy"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.voidedBy')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.remark')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.revision')" path="revision">
          <NInputNumber
            v-model:value="model.revision"
            :placeholder="$t('page.work_ticket_management.work_ticket.form.revision')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.workMonth')" path="workMonthId">
          <NSelect
            v-model:value="model.workMonthId"
            :options="props.workMonthOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket.form.workMonth')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.order')" path="orderId">
          <NSelect
            v-model:value="model.orderId"
            :options="props.orderOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket.form.order')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket.sourceImportRow')" path="sourceImportRowId">
          <NSelect
            v-model:value="model.sourceImportRowId"
            :options="props.sourceImportRowOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket.form.sourceImportRow')"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace :size="16">
          <NButton @click="closeDrawer">{{ $t('common.cancel') }}</NButton>
          <NButton type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</NButton>
        </NSpace>
      </template>
    </NDrawerContent>
  </NDrawer>
</template>
