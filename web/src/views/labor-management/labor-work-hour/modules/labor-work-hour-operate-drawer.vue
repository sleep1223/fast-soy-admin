<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddLaborWorkHour, fetchUpdateLaborWorkHour } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'LaborWorkHourOperateDrawer' });

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.LaborManagementManage.LaborWorkHour | null;
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
    add: $t('page.labor_management.labor_work_hour.addLaborWorkHour'),
    edit: $t('page.labor_management.labor_work_hour.editLaborWorkHour')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.LaborManagementManage.LaborWorkHourAddParams {
  return {
    ticketCode: '',
    workHours: null,
    orderNo: ''
  } as unknown as Api.LaborManagementManage.LaborWorkHourAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  ticketCode: defaultRequiredRule,
  workHours: defaultRequiredRule,
  orderNo: defaultRequiredRule
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
    const { error } = await fetchAddLaborWorkHour(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateLaborWorkHour({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.labor_management.labor_work_hour.ticketCode')" path="ticketCode">
          <NInput
            v-model:value="model.ticketCode"
            :placeholder="$t('page.labor_management.labor_work_hour.form.ticketCode')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.labor_management.labor_work_hour.workHours')" path="workHours">
          <NInputNumber
            v-model:value="model.workHours"
            :precision="2"
            :placeholder="$t('page.labor_management.labor_work_hour.form.workHours')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.labor_management.labor_work_hour.orderNo')" path="orderNo">
          <NInput
            v-model:value="model.orderNo"
            :placeholder="$t('page.labor_management.labor_work_hour.form.orderNo')"
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
