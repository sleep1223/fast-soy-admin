<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddWorker, fetchUpdateWorker } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'WorkerOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.Worker | null;
  productionUnitOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  productionUnitOptions: () => []
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
    add: $t('page.work_ticket_management.worker.addWorker'),
    edit: $t('page.work_ticket_management.worker.editWorker')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.WorkerAddParams {
  return {
    workerNo: '',
    name: '',
    enabled: false,
    remark: '',
    productionUnitId: null
  } as unknown as Api.WorkTicketManagementManage.WorkerAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
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
    const { error } = await fetchAddWorker(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateWorker({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.worker.workerNo')" path="workerNo">
          <NInput
            v-model:value="model.workerNo"
            :placeholder="$t('page.work_ticket_management.worker.form.workerNo')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.name')" path="name">
          <NInput v-model:value="model.name" :placeholder="$t('page.work_ticket_management.worker.form.name')" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.enabled')" path="enabled">
          <NSwitch :value="Boolean(model.enabled)" @update:value="value => (model.enabled = value)" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.remark')" path="remark">
          <NInput v-model:value="model.remark" :placeholder="$t('page.work_ticket_management.worker.form.remark')" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.worker.productionUnit')" path="productionUnitId">
          <NSelect
            v-model:value="model.productionUnitId"
            :options="props.productionUnitOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.worker.form.productionUnit')"
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
