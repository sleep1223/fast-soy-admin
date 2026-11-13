<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddMonthlyImportBatch, fetchUpdateMonthlyImportBatch } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'MonthlyImportBatchOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.MonthlyImportBatch | null;
  sourceTypeOptions?: SelectOptionItem[];
  statusOptions?: SelectOptionItem[];
  workMonthOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  sourceTypeOptions: () => [],
  statusOptions: () => [],
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
    add: $t('page.work_ticket_management.monthly_import_batch.addMonthlyImportBatch'),
    edit: $t('page.work_ticket_management.monthly_import_batch.editMonthlyImportBatch')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.MonthlyImportBatchAddParams {
  return {
    sourceType: '',
    status: '',
    sourceName: '',
    contentHash: '',
    rowCount: null,
    voidReason: '',
    voidedAt: null,
    voidedBy: '',
    remark: '',
    workMonthId: null
  } as unknown as Api.WorkTicketManagementManage.MonthlyImportBatchAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  sourceType: defaultRequiredRule,
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
    const { error } = await fetchAddMonthlyImportBatch(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateMonthlyImportBatch({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.sourceType')" path="sourceType">
          <NSelect
            v-model:value="model.sourceType"
            :options="props.sourceTypeOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.sourceType')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.status')" path="status">
          <NSelect
            v-model:value="model.status"
            :options="props.statusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.status')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.sourceName')" path="sourceName">
          <NInput
            v-model:value="model.sourceName"
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.sourceName')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.contentHash')" path="contentHash">
          <NInput
            v-model:value="model.contentHash"
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.contentHash')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.rowCount')" path="rowCount">
          <NInputNumber
            v-model:value="model.rowCount"
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.rowCount')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.voidReason')" path="voidReason">
          <NInput
            v-model:value="model.voidReason"
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.voidReason')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.voidedAt')" path="voidedAt">
          <NDatePicker
            v-model:formatted-value="model.voidedAt"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.voidedBy')" path="voidedBy">
          <NInput
            v-model:value="model.voidedBy"
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.voidedBy')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.remark')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_batch.workMonth')" path="workMonthId">
          <NSelect
            v-model:value="model.workMonthId"
            :options="props.workMonthOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_batch.form.workMonth')"
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
