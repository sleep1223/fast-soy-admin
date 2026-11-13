<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddWorkMonth, fetchUpdateWorkMonth } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'WorkMonthOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.WorkTicketManagementManage.WorkMonth | null;
  statusOptions?: SelectOptionItem[];
  productionUnitOptions?: SelectOptionItem[];
}

const props = withDefaults(defineProps<Props>(), {
  statusOptions: () => [],
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
    add: $t('page.work_ticket_management.work_month.addWorkMonth'),
    edit: $t('page.work_ticket_management.work_month.editWorkMonth')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.WorkTicketManagementManage.WorkMonthAddParams {
  return {
    yearMonth: '',
    status: '',
    remark: '',
    revision: null,
    closedAt: null,
    closedBy: '',
    reopenedAt: null,
    reopenCount: null,
    productionUnitId: null
  } as unknown as Api.WorkTicketManagementManage.WorkMonthAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  yearMonth: defaultRequiredRule,
  productionUnitId: defaultRequiredRule
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
    const { error } = await fetchAddWorkMonth(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateWorkMonth({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.work_ticket_management.work_month.yearMonth')" path="yearMonth">
          <NInput
            v-model:value="model.yearMonth"
            :placeholder="$t('page.work_ticket_management.work_month.form.yearMonth')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.status')" path="status">
          <NSelect
            v-model:value="model.status"
            :options="props.statusOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_month.form.status')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.remark')" path="remark">
          <NInput
            v-model:value="model.remark"
            :placeholder="$t('page.work_ticket_management.work_month.form.remark')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.revision')" path="revision">
          <NInputNumber
            v-model:value="model.revision"
            :placeholder="$t('page.work_ticket_management.work_month.form.revision')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.closedAt')" path="closedAt">
          <NDatePicker
            v-model:formatted-value="model.closedAt"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.closedBy')" path="closedBy">
          <NInput
            v-model:value="model.closedBy"
            :placeholder="$t('page.work_ticket_management.work_month.form.closedBy')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.reopenedAt')" path="reopenedAt">
          <NDatePicker
            v-model:formatted-value="model.reopenedAt"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.reopenCount')" path="reopenCount">
          <NInputNumber
            v-model:value="model.reopenCount"
            :placeholder="$t('page.work_ticket_management.work_month.form.reopenCount')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.work_ticket_management.work_month.productionUnit')" path="productionUnitId">
          <NSelect
            v-model:value="model.productionUnitId"
            :options="props.productionUnitOptions"
            clearable
            filterable
            :placeholder="$t('page.work_ticket_management.work_month.form.productionUnit')"
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
