<script setup lang="ts">
import { ref } from 'vue';
import { $t } from '@/locales';

// import { computed } from 'vue';
// import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { logTypeOptions } from '@/constants/business';
import { translateOptions } from '@/utils/common';
import { useNaiveForm } from '@/hooks/common/form';
import { useAuth } from '@/hooks/business/auth';
defineOptions({
  name: 'LogSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const { hasAuth } = useAuth();
const { formRef, validate, restoreValidation } = useNaiveForm();

const model = defineModel<Api.SystemManage.LogSearchParams>('model', { required: true });

const timeRange = ref<[number, number]>([new Date().setHours(0, 0, 0, 0), Date.now()]);

// type RuleKey = Extract<keyof Api.SystemManage.LogSearchParams, 'logEmail' | 'logPhone'>;

// const rules = computed<Record<RuleKey, App.Global.FormRule>>(() => {
//   const { patternRules } = useFormRules(); // inside computed to make locale reactive

//   return {
//     path: patternRules.path
//   };
// });

async function reset() {
  await restoreValidation();
  emit('reset');
}

async function search() {
  await validate();
  if (timeRange.value) {
    model.value.timeRange = timeRange.value.join(',');
  }

  emit('search');
}
</script>

<template>
  <NCard :title="$t('common.search')" :bordered="false" size="small" class="card-wrapper">
    <!-- <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="80"> -->
    <NForm ref="formRef" :model="model" label-placement="left" :label-width="100">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi
          v-show="hasAuth('B_Add_Del_Batch-del')"
          span="24 s:12 m:6"
          :label="$t('page.manage.log.logType')"
          path="logType"
          class="pr-24px"
        >
          <NSelect
            v-model:value="model.logType"
            :placeholder="$t('page.manage.log.form.logType')"
            :options="translateOptions(logTypeOptions)"
            clearable
          />
        </NFormItemGi>

        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.log.logUser')" path="logUser" class="pr-24px">
          <NInput v-model:value="model.logUser" :placeholder="$t('page.manage.log.form.logUser')" />
        </NFormItemGi>
        <NFormItemGi
          span="24 s:12 m:6"
          :label="$t('page.manage.log.logDetailType')"
          path="logDetailType"
          class="pr-24px"
        >
          <NInput v-model:value="model.logDetailType" :placeholder="$t('page.manage.log.form.logDetailType')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.log.requestUrl')" path="requestUrl" class="pr-24px">
          <NInput v-model:value="model.requestUrl" :placeholder="$t('page.manage.log.form.requestUrl')" />
        </NFormItemGi>

        <NFormItemGi span="24 s:12 m:9" :label="$t('page.manage.log.createTime')" path="createTime" class="pr-24px">
          <NDatePicker v-model:value="timeRange" type="datetimerange" clearable />
        </NFormItemGi>

        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.log.responseCode')" path="responseCode" class="pr-24px">
          <NInput v-model:value="model.responseCode" :placeholder="$t('page.manage.log.form.responseCode')" />
        </NFormItemGi>

        <NFormItemGi span="24 m:8" class="pr-24px">
          <NSpace class="w-full" justify="end">
            <NButton @click="reset">
              <template #icon>
                <icon-ic-round-refresh class="text-icon" />
              </template>
              {{ $t('common.reset') }}
            </NButton>
            <NButton type="primary" ghost @click="search">
              <template #icon>
                <icon-ic-round-search class="text-icon" />
              </template>
              {{ $t('common.search') }}
            </NButton>
          </NSpace>
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped></style>
