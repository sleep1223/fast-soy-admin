<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddLaborWorker, fetchUpdateLaborWorker } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'LaborWorkerOperateDrawer' });

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.LaborManagementManage.LaborWorker | null;
}

const props = defineProps<Props>();

interface Emits {
  (e: 'submitted'): void;
}

const emit = defineEmits<Emits>();
const visible = defineModel<boolean>('visible', { default: false });
const { formRef, validate, restoreValidation } = useNaiveForm();
const { defaultRequiredRule } = useFormRules();

const title = computed(() => {
  const titles: Record<NaiveUI.TableOperateType, string> = {
    add: $t('page.labor_management.labor_worker.addLaborWorker'),
    edit: $t('page.labor_management.labor_worker.editLaborWorker')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.LaborManagementManage.LaborWorkerAddParams {
  return {
    employeeNo: '',
    trade: '',
    name: '',
    remark: ''
  } as unknown as Api.LaborManagementManage.LaborWorkerAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  employeeNo: defaultRequiredRule,
  trade: defaultRequiredRule,
  name: defaultRequiredRule
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
    const { error } = await fetchAddLaborWorker(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateLaborWorker({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.labor_management.labor_worker.employeeNo')" path="employeeNo">
          <NInput
            v-model:value="model.employeeNo"
            :placeholder="$t('page.labor_management.labor_worker.form.employeeNo')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.labor_management.labor_worker.trade')" path="trade">
          <NInput v-model:value="model.trade" :placeholder="$t('page.labor_management.labor_worker.form.trade')" />
        </NFormItem>
        <NFormItem :label="$t('page.labor_management.labor_worker.name')" path="name">
          <NInput v-model:value="model.name" :placeholder="$t('page.labor_management.labor_worker.form.name')" />
        </NFormItem>
        <NFormItem :label="$t('page.labor_management.labor_worker.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            type="textarea"
            :placeholder="$t('page.labor_management.labor_worker.form.remark')"
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
