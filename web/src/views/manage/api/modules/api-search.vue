<script setup lang="ts">
import { $t } from '@/locales';

// import { computed } from 'vue';
// import { useFormRules, useNaiveForm } from '@/hooks/common/form';
import { apiMethodOptions, enableStatusOptions } from '@/constants/business';
import { translateOptions } from '@/utils/common';
import { useNaiveForm } from '@/hooks/common/form';

defineOptions({
  name: 'ApiSearch'
});

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();

const { formRef, validate, restoreValidation } = useNaiveForm();

const model = defineModel<Api.SystemManage.ApiSearchParams>('model', { required: true });

// type RuleKey = Extract<keyof Api.SystemManage.ApiSearchParams, 'apiEmail' | 'apiPhone'>;

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
  emit('search');
}
</script>

<template>
  <NCard :title="$t('common.search')" :bordered="false" size="small" class="card-wrapper">
    <!-- <NForm ref="formRef" :model="model" :rules="rules" label-placement="left" :label-width="80"> -->
    <NForm ref="formRef" :model="model" label-placement="left" :label-width="80">
      <NGrid responsive="screen" item-responsive>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.api.method')" path="method" class="pr-24px">
          <NSelect
            v-model:value="model.method"
            :placeholder="$t('page.manage.api.form.method')"
            :options="translateOptions(apiMethodOptions)"
            clearable
          />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.api.path')" path="path" class="pr-24px">
          <NInput v-model:value="model.path" :placeholder="$t('page.manage.api.form.path')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.api.summary')" path="summary" class="pr-24px">
          <NInput v-model:value="model.summary" :placeholder="$t('page.manage.api.form.summary')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.api.tags')" path="tags" class="pr-24px">
          <NInput v-model:value="model.tags" :placeholder="$t('page.manage.api.form.tags')" />
        </NFormItemGi>
        <NFormItemGi span="24 s:12 m:6" :label="$t('page.manage.api.status')" path="status" class="pr-24px">
          <NSelect
            v-model:value="model.status"
            :placeholder="$t('page.manage.api.form.status')"
            :options="translateOptions(enableStatusOptions)"
            clearable
          />
        </NFormItemGi>
        <NFormItemGi span="24 m:18" class="pr-24px">
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
