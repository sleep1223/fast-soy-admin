<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddWorkMonthStatusLog, fetchUpdateWorkMonthStatusLog } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'WorkMonthStatusLogOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.WorkMonthStatusLog | null;
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

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();
const visible = defineModel<boolean>('visible', { default: false });
const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.work_ticket_management.work_month_status_log.addWorkMonthStatusLog'),
    edit: $t('page.work_ticket_management.work_month_status_log.editWorkMonthStatusLog')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.WorkMonthStatusLogAddParams {
  return {
    fromStatus: '',
    toStatus: '',
    action: '',
    reason: '',
    summary: null,
    workMonthId: null
  } as unknown as Api.WorkTicketManagementManage.WorkMonthStatusLogAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  toStatus: defaultRequiredRule,
  action: defaultRequiredRule,
  workMonthId: defaultRequiredRule
};

function formatJsonInput(value: unknown): string {
  if (value === null || value === undefined || value === '') return '';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

function parseJsonInput(value: string): Record<string, any> | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return JSON.parse(trimmed) as Record<string, any>;
}

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
    const { error } = await fetchAddWorkMonthStatusLog(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateWorkMonthStatusLog({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.work_month_status_log.fromStatus')" path="fromStatus">
          <NSelect
            v-model:value="model.fromStatus"
            :options="props.fromStatusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_month_status_log.form.fromStatus')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month_status_log.toStatus')" path="toStatus">
          <NSelect
            v-model:value="model.toStatus"
            :options="props.toStatusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_month_status_log.form.toStatus')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month_status_log.action')" path="action">
          <NSelect
            v-model:value="model.action"
            :options="props.actionOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_month_status_log.form.action')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month_status_log.reason')" path="reason">
          <NInput
            v-model:value="model.reason"
            :placeholder="$t('page.work_ticket_management.work_month_status_log.form.reason')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month_status_log.summary')" path="summary">
          <NInput
            :value="formatJsonInput(model.summary)"
            type="textarea"
            :placeholder="$t('page.work_ticket_management.work_month_status_log.form.summary')"
            @update:value="value => (model.summary = parseJsonInput(value))"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month_status_log.workMonth')" path="workMonthId">
          <NSelect
            v-model:value="model.workMonthId"
            :options="props.workMonthOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_month_status_log.form.workMonth')"
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
