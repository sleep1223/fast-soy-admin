<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddWorkTicketAssignment, fetchUpdateWorkTicketAssignment } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'WorkTicketAssignmentOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.WorkTicketAssignment | null;
  sourceOptions?: SelectOptionItem[];
  ticketOptions?: SelectOptionItem[];
  workerOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  sourceOptions: () => [],
  ticketOptions: () => [],
  workerOptions: () => []
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
    add: $t('page.work_ticket_management.work_ticket_assignment.addWorkTicketAssignment'),
    edit: $t('page.work_ticket_management.work_ticket_assignment.editWorkTicketAssignment')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.WorkTicketAssignmentAddParams {
  return {
    source: '',
    remark: '',
    ticketId: null,
    workerId: null
  } as unknown as Api.WorkTicketManagementManage.WorkTicketAssignmentAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  ticketId: defaultRequiredRule,
  workerId: defaultRequiredRule
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
    const { error } = await fetchAddWorkTicketAssignment(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateWorkTicketAssignment({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.work_ticket_assignment.source')" path="source">
          <NSelect
            v-model:value="model.source"
            :options="props.sourceOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.source')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket_assignment.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.remark')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket_assignment.ticket')" path="ticketId">
          <NSelect
            v-model:value="model.ticketId"
            :options="props.ticketOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.ticket')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_ticket_assignment.worker')" path="workerId">
          <NSelect
            v-model:value="model.workerId"
            :options="props.workerOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_ticket_assignment.form.worker')"
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
