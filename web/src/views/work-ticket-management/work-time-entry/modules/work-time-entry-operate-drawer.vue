<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddWorkTimeEntry, fetchUpdateWorkTimeEntry } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'WorkTimeEntryOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.WorkTimeEntry | null;
  assignmentOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  assignmentOptions: () => []
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
    add: $t('page.work_ticket_management.work_time_entry.addWorkTimeEntry'),
    edit: $t('page.work_ticket_management.work_time_entry.editWorkTimeEntry')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.WorkTimeEntryAddParams {
  return {
    workDate: null,
    accountingMonth: '',
    hours: null,
    remark: '',
    assignmentId: null
  } as unknown as Api.WorkTicketManagementManage.WorkTimeEntryAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  workDate: defaultRequiredRule,
  hours: defaultRequiredRule,
  assignmentId: defaultRequiredRule
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
    const { error } = await fetchAddWorkTimeEntry(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateWorkTimeEntry({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.work_time_entry.workDate')" path="workDate">
          <NDatePicker
            v-model:formatted-value="model.workDate"
            type="date"
            value-format="yyyy-MM-dd"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_time_entry.accountingMonth')" path="accountingMonth">
          <NInput
            v-model:value="model.accountingMonth"
            :placeholder="$t('page.work_ticket_management.work_time_entry.form.accountingMonth')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_time_entry.hours')" path="hours">
          <NInputNumber
            v-model:value="model.hours"
            :precision="2"
            :placeholder="$t('page.work_ticket_management.work_time_entry.form.hours')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_time_entry.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            :placeholder="$t('page.work_ticket_management.work_time_entry.form.remark')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_time_entry.assignment')" path="assignmentId">
          <NSelect
            v-model:value="model.assignmentId"
            :options="props.assignmentOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_time_entry.form.assignment')"
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
