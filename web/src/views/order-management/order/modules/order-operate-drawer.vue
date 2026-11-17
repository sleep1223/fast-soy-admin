<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { jsonClone } from '@sa/utils';
import { fetchAddOrder, fetchUpdateOrder } from '@/service/api';
import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';

defineOptions({ name: 'OrderOperateDrawer' });

interface Props {
  operateType: NaiveUI.TableOperateType;
  rowData?: Api.OrderManagementManage.Order | null;
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
    add: $t('page.order_management.order.addOrder'),
    edit: $t('page.order_management.order.editOrder')
  };
  return titles[props.operateType];
});

const model = ref(createDefaultModel());

function createDefaultModel(): Api.OrderManagementManage.OrderAddParams {
  return {
    orderNo: '',
    partNo: '',
    name: '',
    netWeight: null,
    grossWeight: null,
    unit: '',
    quantity: null,
    receivedQuantity: null,
    totalWeight: null,
    orderDueDate: null,
    completedDate: null,
    processRoute: '',
    customer: ''
  } as unknown as Api.OrderManagementManage.OrderAddParams;
}

const rules: Record<string, App.Global.FormRule> = {
  orderNo: defaultRequiredRule,
  partNo: defaultRequiredRule,
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
    const { error } = await fetchAddOrder(model.value);
    if (error) return;
    window.$message?.success($t('common.addSuccess'));
  } else {
    const { error } = await fetchUpdateOrder({ id: props.rowData?.id, ...model.value });
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
        <NFormItem :label="$t('page.order_management.order.orderNo')" path="orderNo">
          <NInput v-model:value="model.orderNo" :placeholder="$t('page.order_management.order.form.orderNo')" />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.partNo')" path="partNo">
          <NInput v-model:value="model.partNo" :placeholder="$t('page.order_management.order.form.partNo')" />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.name')" path="name">
          <NInput v-model:value="model.name" :placeholder="$t('page.order_management.order.form.name')" />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.netWeight')" path="netWeight">
          <NInputNumber
            v-model:value="model.netWeight"
            :precision="6"
            :placeholder="$t('page.order_management.order.form.netWeight')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.grossWeight')" path="grossWeight">
          <NInputNumber
            v-model:value="model.grossWeight"
            :precision="6"
            :placeholder="$t('page.order_management.order.form.grossWeight')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.unit')" path="unit">
          <NInput v-model:value="model.unit" :placeholder="$t('page.order_management.order.form.unit')" />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.quantity')" path="quantity">
          <NInputNumber
            v-model:value="model.quantity"
            :placeholder="$t('page.order_management.order.form.quantity')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.receivedQuantity')" path="receivedQuantity">
          <NInputNumber
            v-model:value="model.receivedQuantity"
            :placeholder="$t('page.order_management.order.form.receivedQuantity')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.totalWeight')" path="totalWeight">
          <NInputNumber
            v-model:value="model.totalWeight"
            :precision="2"
            :placeholder="$t('page.order_management.order.form.totalWeight')"
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.orderDueDate')" path="orderDueDate">
          <NDatePicker
            v-model:formatted-value="model.orderDueDate"
            type="date"
            value-format="yyyy-MM-dd"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.completedDate')" path="completedDate">
          <NDatePicker
            v-model:formatted-value="model.completedDate"
            type="date"
            value-format="yyyy-MM-dd"
            clearable
            class="w-full"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.processRoute')" path="processRoute">
          <NInput
            v-model:value="model.processRoute"
            :placeholder="$t('page.order_management.order.form.processRoute')"
          />
        </NFormItem>
        <NFormItem :label="$t('page.order_management.order.customer')" path="customer">
          <NInput v-model:value="model.customer" :placeholder="$t('page.order_management.order.form.customer')" />
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
