<script setup lang="ts">
import { reactive, watch } from 'vue';
import { useNaiveForm } from '@/hooks/common/form';
import { $t } from '@/locales';
import { logTypeOptions } from '@/constants/business';

defineOptions({
  name: 'LogOperateDrawer'
});

interface Props {
  /** the type of operation */
  operateType: NaiveUI.TableOperateType;
  /** the edit row data */
  rowData?: Api.SystemManage.Log | null;
}

const props = defineProps<Props>();

const visible = defineModel<boolean>('visible', {
  default: false
});

const { formRef, restoreValidation } = useNaiveForm();

const title = $t('page.manage.log.viewLog');

const model: Api.SystemManage.LogUpdateParams = reactive(createDefaultModel());

function createDefaultModel(): Api.SystemManage.LogUpdateParams {
  return {
    logType: '1',
    logUser: '',
    logDetailType: null,
    requestUrl: '',
    createTime: '',
    responseCode: ''
  };
}

function handleInitModel() {
  Object.assign(model, createDefaultModel());

  if (props.operateType === 'edit' && props.rowData) {
    Object.assign(model, props.rowData);
  }
}

watch(visible, () => {
  if (visible.value) {
    handleInitModel();
    restoreValidation();
  }
});
</script>

<template>
  <NDrawer v-model:show="visible" display-directive="show" :width="360">
    <NDrawerContent :title="title" :native-scrollbar="false" closable>
      <NForm ref="formRef" :model="model">
        <NFormItem :label="$t('page.manage.log.logType')" path="logType">
          <NRadioGroup v-model:value="model.logType">
            <NRadio v-for="item in logTypeOptions" :key="item.value" :value="item.value" :label="$t(item.label)" />
          </NRadioGroup>
        </NFormItem>
        <NFormItem :label="$t('page.manage.log.logUser')" path="logUser">
          <NInput v-model:value="model.logUser" :placeholder="$t('page.manage.log.form.logUser')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.log.logDetailType')" path="logDetailType">
          <NInput v-model:value="model.logDetailType" :placeholder="$t('page.manage.log.form.logDetailType')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.log.requestUrl')" path="requestUrl">
          <NInput v-model:value="model.requestUrl" :placeholder="$t('page.manage.log.form.requestUrl')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.log.createTime')" path="createTime">
          <NInput v-model:value="model.createTime" :placeholder="$t('page.manage.log.form.createTime')" />
        </NFormItem>
        <NFormItem :label="$t('page.manage.log.responseCode')" path="responseCode">
          <NInput v-model:value="model.responseCode" :placeholder="$t('page.manage.log.form.responseCode')" />
        </NFormItem>
      </NForm>
    </NDrawerContent>
  </NDrawer>
</template>

<style scoped></style>
