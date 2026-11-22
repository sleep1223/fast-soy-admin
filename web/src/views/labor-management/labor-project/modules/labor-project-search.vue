<script setup lang="ts">
import { computed } from 'vue';
import { $t } from '@/locales';

defineOptions({ name: 'LaborProjectSearch' });

interface Emits {
  (e: 'reset'): void;
  (e: 'search'): void;
}

const emit = defineEmits<Emits>();
const model = defineModel<Api.LaborManagementManage.LaborProjectSearchParams>('model', { required: true });
const importedRange = computed<[number, number] | null>({
  get: () =>
    model.value.importedAtStart && model.value.importedAtEnd
      ? ([new Date(model.value.importedAtStart).getTime(), new Date(model.value.importedAtEnd).getTime()] as [
          number,
          number
        ])
      : null,
  set: (value: [number, number] | null) => {
    model.value.importedAtStart = value ? new Date(value[0]).toISOString() : null;
    model.value.importedAtEnd = value ? new Date(value[1]).toISOString() : null;
  }
});
const paintingValue = computed({
  get: () => (model.value.skipPainting == null ? 'all' : model.value.skipPainting ? 'skip' : 'required'),
  set: (value: string) => {
    model.value.skipPainting = value === 'all' ? null : value === 'skip';
  }
});
const paintingOptions = computed(() => [
  { label: $t('page.labor_management.labor_project.paintingRequired'), value: 'required' },
  { label: $t('page.labor_management.labor_project.skipPainting'), value: 'skip' },
  { label: $t('page.labor_management.labor_project.paintingAll'), value: 'all' }
]);

function reset() {
  emit('reset');
}

function search() {
  emit('search');
}
</script>

<template>
  <NCard :bordered="false" size="small" class="card-wrapper">
    <NCollapse :default-expanded-names="['labor-project-search']">
      <NCollapseItem :title="$t('common.search')" name="labor-project-search">
        <NForm :model="model" label-placement="left" :label-width="80" @submit.prevent="search">
          <NGrid responsive="screen" item-responsive>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_project.partNo')"
              path="partNo"
              class="pr-24px"
            >
              <NInput
                v-model:value="model.partNo"
                :placeholder="$t('page.labor_management.labor_project.form.partNo')"
              />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:24 m:12"
              :label="$t('page.labor_management.labor_project.importedAt')"
              class="pr-24px"
            >
              <NDatePicker v-model:value="importedRange" type="datetimerange" clearable class="w-full" />
            </NFormItemGi>
            <NFormItemGi
              span="24 s:12 m:6"
              :label="$t('page.labor_management.labor_project.paintingStatus')"
              path="skipPainting"
              class="pr-24px"
            >
              <NSelect v-model:value="paintingValue" :options="paintingOptions" />
            </NFormItemGi>
            <NFormItemGi span="24 s:12 m:6">
              <NSpace class="w-full" justify="end">
                <NButton @click="reset">
                  <template #icon><icon-ic-round-refresh class="text-icon" /></template>
                  {{ $t('common.reset') }}
                </NButton>
                <NButton type="primary" attr-type="submit" ghost>
                  <template #icon><icon-ic-round-search class="text-icon" /></template>
                  {{ $t('common.search') }}
                </NButton>
              </NSpace>
            </NFormItemGi>
          </NGrid>
        </NForm>
      </NCollapseItem>
    </NCollapse>
  </NCard>
</template>
