<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddProductionUnit, fetchUpdateProductionUnit } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'ProductionUnitOperateDrawer' });

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.ProductionUnit | null;
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
    add: $t('page.work_ticket_management.production_unit.addProductionUnit'),
    edit: $t('page.work_ticket_management.production_unit.editProductionUnit')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.ProductionUnitAddParams {
  return {
    code: '',
    name: '',
    enabled: false,
    remark: ''
  } as unknown as Api.WorkTicketManagementManage.ProductionUnitAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  code: defaultRequiredRule,
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
    const { error } = await fetchAddProductionUnit(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateProductionUnit({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.production_unit.code')" path="code">
          <NInput
            v-model:value="model.code"
            :placeholder="$t('page.work_ticket_management.production_unit.form.code')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.production_unit.name')" path="name">
          <NInput
            v-model:value="model.name"
            :placeholder="$t('page.work_ticket_management.production_unit.form.name')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.production_unit.enabled')" path="enabled">
          <NSwitch :value="Boolean(model.enabled)" @update:value="value => (model.enabled = value)" />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.production_unit.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            :placeholder="$t('page.work_ticket_management.production_unit.form.remark')"
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
