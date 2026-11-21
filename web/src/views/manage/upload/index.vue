<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import ImageUpload from '@/components/advanced/image-upload.vue';
import { fetchUploadSettings, fetchUpdateUploadSettings } from '@/service/api/upload';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import ImageLibrary from './modules/image-library.vue';

defineOptions({ name: 'UploadManage' });

const { hasAuth } = useAuth();
const settings = reactive({ storageRoot: '', maxSizeMb: 5 });
const settingsReady = ref(false);
const saving = ref(false);
const busy = ref(false);
const uploadVisible = ref(false);
const uploadValue = ref('');
const library = ref<InstanceType<typeof ImageLibrary>>();

async function saveSettings() {
  if (saving.value || busy.value || !settings.storageRoot.trim()) return;

  saving.value = true;
  try {
    const { data, error } = await fetchUpdateUploadSettings(settings);
    if (!error && data) {
      Object.assign(settings, data);
      window.$message?.success($t('common.updateSuccess'));
    }
  } finally {
    saving.value = false;
  }
}

function openUpload() {
  uploadValue.value = '';
  uploadVisible.value = true;
}

onMounted(async () => {
  const { data, error } = await fetchUploadSettings();
  if (!error && data) {
    Object.assign(settings, data);
    settingsReady.value = true;
  }
});
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="card-wrapper">
      <NCollapse>
        <NCollapseItem :title="$t('imageTools.settings')" name="settings">
          <NAlert type="info" class="mb-4">{{ $t('imageTools.directoryHint') }}</NAlert>
          <NForm
            label-placement="left"
            :label-width="100"
            :disabled="!settingsReady || saving || !hasAuth('B_SYSTEM_UPLOAD_CONFIG')"
          >
            <NGrid responsive="screen" item-responsive>
              <NFormItemGi span="24 m:16" :label="$t('imageTools.directory')" class="pr-24px">
                <NInput v-model:value="settings.storageRoot" :maxlength="1000" />
              </NFormItemGi>
              <NFormItemGi span="24 m:6" :label="$t('imageTools.maxSize')" class="pr-24px">
                <NInputNumber v-model:value="settings.maxSizeMb" :min="1" :max="20" class="w-full" />
              </NFormItemGi>
              <NFormItemGi v-if="hasAuth('B_SYSTEM_UPLOAD_CONFIG')" span="24 m:2" class="pr-24px" justify="end">
                <NSpace class="w-full" justify="end">
                  <NButton
                    type="primary"
                    :loading="saving"
                    :disabled="busy || !settingsReady || !settings.storageRoot.trim()"
                    @click="saveSettings"
                  >
                    {{ $t('common.confirm') }}
                  </NButton>
                </NSpace>
              </NFormItemGi>
            </NGrid>
          </NForm>
        </NCollapseItem>
      </NCollapse>
    </NCard>

    <ImageLibrary ref="library" @add="openUpload" />

    <NModal v-model:show="uploadVisible" preset="card" :title="$t('imageTools.add')" class="w-160 max-w-95vw">
      <ImageUpload
        v-if="uploadVisible"
        v-model:value="uploadValue"
        v-model:busy="busy"
        :limit="10"
        @update:value="() => library?.refresh()"
      />
    </NModal>
  </div>
</template>
