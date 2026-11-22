<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddLaborWorkHour, fetchOcrRecognize, fetchUpdateLaborWorkHour } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'LaborWorkHourOperateDrawer' });

type SelectOptionItem = { label: string; value: string | number };

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.LaborManagementManage.LaborWorkHour | null;
  workerOptions?: SelectOptionItem[];
  initialOrderNo?: string;
}

const props = withDefaults(defineProps<Props>(), {
  rowData: null,
  initialOrderNo: '',
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
    add: $t('page.labor_management.labor_work_hour.addLaborWorkHour'),
    edit: $t('page.labor_management.labor_work_hour.editLaborWorkHour')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());
const ocrOptions = ref<{ label: string; value: string }[]>([]);
const ocrLoading = ref(false);
let ocrSession = 0;

async function recognizeTicket(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (!file) return;
  const current = ++ocrSession;
  ocrLoading.value = true;
  ocrOptions.value = [];
  try {
    const { data, error } = await fetchOcrRecognize(file);
    if (current !== ocrSession || error || !data) return;
    ocrOptions.value = [...new Set(data.items.map(item => item.text.trim()).filter(Boolean))].map(value => ({
      label: value,
      value
    }));
    if (!ocrOptions.value.length) window.$message?.warning($t('page.labor_management.labor_work_hour.ocrEmpty'));
  } finally {
    if (current === ocrSession) ocrLoading.value = false;
  }
}

function createDefaultModel(): Api.LaborManagementManage.LaborWorkHourAddParams {
  return {
    ticketCode: '',
    workHours: null,
    orderNo: props.initialOrderNo,
    workerId: null
  } as unknown as Api.LaborManagementManage.LaborWorkHourAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  ticketCode: defaultRequiredRule,
  workHours: defaultRequiredRule,
  orderNo: defaultRequiredRule,
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
  ocrSession += 1;
  ocrLoading.value = false;
  ocrOptions.value = [];
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
          <NSpace vertical class="w-full">
            <NInput
              v-model:value="model.ticketCode"
              :placeholder="$t('page.labor_management.labor_work_hour.form.ticketCode')"
            />
            <label>
              {{ $t('page.labor_management.labor_work_hour.ocrUpload') }}
              <input type="file" accept="image/*" :disabled="ocrLoading" @change="recognizeTicket" />
            </label>
            <NSelect
              v-if="ocrOptions.length"
              :options="ocrOptions"
              :placeholder="$t('page.labor_management.labor_work_hour.ocrSelect')"
              @update:value="value => (model.ticketCode = value)"
            />
          </NSpace>
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
        <NFormItem :label="$t('page.labor_management.labor_work_hour.worker')" path="workerId">
          <NSelect
            v-model:value="model.workerId"
            :options="props.workerOptions"
            clearable
            filterable
            :placeholder="$t('page.labor_management.labor_work_hour.form.worker')"
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
