<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddMonthlyImportRow, fetchUpdateMonthlyImportRow } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'MonthlyImportRowOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.MonthlyImportRow | null;
  matchStatusOptions?: SelectOptionItem[];
  matchSourceOptions?: SelectOptionItem[];
  handlingStatusOptions?: SelectOptionItem[];
  batchOptions?: SelectOptionItem[];
  orderOptions?: SelectOptionItem[];
  duplicateOfRowOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  matchStatusOptions: () => [],
  matchSourceOptions: () => [],
  handlingStatusOptions: () => [],
  batchOptions: () => [],
  orderOptions: () => [],
  duplicateOfRowOptions: () => []
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
    add: $t('page.work_ticket_management.monthly_import_row.addMonthlyImportRow'),
    edit: $t('page.work_ticket_management.monthly_import_row.editMonthlyImportRow')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.MonthlyImportRowAddParams {
  return {
    rowNumber: null,
    rawPartNo: '',
    normalizedPartNo: '',
    matchStatus: '',
    matchSource: '',
    sourceQuantity: null,
    rawData: null,
    handlingStatus: '',
    handlingNote: '',
    handledAt: null,
    handledBy: '',
    note: '',
    batchId: null,
    orderId: null,
    duplicateOfRowId: null
  } as unknown as Api.WorkTicketManagementManage.MonthlyImportRowAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  rowNumber: defaultRequiredRule,
  rawPartNo: defaultRequiredRule,
  normalizedPartNo: defaultRequiredRule,
  batchId: defaultRequiredRule
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
    const { error } = await fetchAddMonthlyImportRow(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateMonthlyImportRow({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.rowNumber')" path="rowNumber">
          <NInputNumber
            v-model:value="model.rowNumber"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.rowNumber')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.rawPartNo')" path="rawPartNo">
          <NInput
            v-model:value="model.rawPartNo"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.rawPartNo')"
          />
        </NFormItem>
        <NFormItem
          :label="$t('page.work_ticket_management.monthly_import_row.normalizedPartNo')"
          path="normalizedPartNo"
        >
          <NInput
            v-model:value="model.normalizedPartNo"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.normalizedPartNo')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.matchStatus')" path="matchStatus">
          <NSelect
            v-model:value="model.matchStatus"
            :options="props.matchStatusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.matchStatus')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.matchSource')" path="matchSource">
          <NSelect
            v-model:value="model.matchSource"
            :options="props.matchSourceOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.matchSource')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.sourceQuantity')" path="sourceQuantity">
          <NInputNumber
            v-model:value="model.sourceQuantity"
            :precision="2"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.sourceQuantity')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.rawData')" path="rawData">
          <NInput
            :value="formatJsonInput(model.rawData)"
            type="textarea"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.rawData')"
            @update:value="value => (model.rawData = parseJsonInput(value))"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.handlingStatus')" path="handlingStatus">
          <NSelect
            v-model:value="model.handlingStatus"
            :options="props.handlingStatusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.handlingStatus')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.handlingNote')" path="handlingNote">
          <NInput
            v-model:value="model.handlingNote"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.handlingNote')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.handledAt')" path="handledAt">
          <NDatePicker
            v-model:formatted-value="model.handledAt"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.handledBy')" path="handledBy">
          <NInput
            v-model:value="model.handledBy"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.handledBy')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.note')" path="note">
          <NInput
            v-model:value="model.note"
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.note')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.batch')" path="batchId">
          <NSelect
            v-model:value="model.batchId"
            :options="props.batchOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.batch')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.order')" path="orderId">
          <NSelect
            v-model:value="model.orderId"
            :options="props.orderOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.order')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.monthly_import_row.duplicateOfRow')" path="duplicateOfRowId">
          <NSelect
            v-model:value="model.duplicateOfRowId"
            :options="props.duplicateOfRowOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.monthly_import_row.form.duplicateOfRow')"
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
