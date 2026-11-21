<script setup lang="tsx">
import { computed, ref, watch } from 'vue';
import { NButton, NPopconfirm } from 'naive-ui';
import ImagePreview from '@/components/advanced/image-preview.vue';
import { fetchDeleteImages, fetchUploadedImage, fetchUploadedImages, fetchUpdateImage } from '@/service/api/upload';
import type { ImageSearch as ImageSearchParams, UploadedImage } from '@/service/api/upload';
import { useAuth } from '@/hooks/business/auth';
import { useAppStore } from '@/store/modules/app';
import { defaultTransform, useNaivePaginatedTable } from '@/hooks/common/table';
import { imageSrc } from '@/utils/image';
import { $t } from '@/locales';
import ImageSearch from './image-search.vue';

defineOptions({ name: 'ImageLibrary' });

const emit = defineEmits<{ add: [] }>();
const { hasAuth } = useAuth();
const appStore = useAppStore();
const query = ref<ImageSearchParams>({ current: 1, size: 10, name: '', mediaType: null });
const timeRange = ref<[string, string] | null>(null);
const selected = ref<string[]>([]);
const deleting = ref(false);
const editing = ref<UploadedImage | null>(null);
const editName = ref('');
const saving = ref(false);
const detail = ref<UploadedImage | null>(null);
const detailLoading = ref(false);
let detailVersion = 0;

const canDelete = computed(() => hasAuth('B_SYSTEM_UPLOAD_DELETE'));
const canEdit = computed(() => hasAuth('B_SYSTEM_UPLOAD_EDIT'));

const { columns, columnChecks, data, getData, getDataByPage, loading, mobilePagination, pagination, scrollX } = useNaivePaginatedTable({
  api: () => fetchUploadedImages({
    ...query.value,
    createdAtStart: timeRange.value?.[0],
    createdAtEnd: timeRange.value?.[1]
  }),
  transform: response => defaultTransform<UploadedImage>(response),
  onPaginationParamsChange: params => {
    query.value.current = params.page ?? 1;
    query.value.size = params.pageSize ?? 10;
  },
  columns: () => [
    { type: 'selection', width: 48, disabled: () => !canDelete.value || deleting.value },
    { key: 'preview', title: $t('imageTools.thumbnail'), width: 90, render: row => <ImagePreview value={row.url} width={48} height={48} /> },
    { key: 'name', title: $t('imageTools.name'), minWidth: 180, ellipsis: { tooltip: true } },
    { key: 'mediaType', title: $t('imageTools.format'), width: 100, render: row => row.mediaType.replace('image/', '').toUpperCase() },
    { key: 'size', title: $t('imageTools.fileSize'), width: 110, render: row => formatSize(row.size) },
    { key: 'dimensions', title: $t('imageTools.dimensions'), width: 130, render: row => `${row.width} × ${row.height}` },
    { key: 'uploader', title: $t('imageTools.uploader'), minWidth: 120, render: row => row.uploader || '—' },
    { key: 'fmtCreatedAt', title: $t('imageTools.uploadTime'), width: 180 },
    {
      key: 'operate',
      title: $t('common.operate'),
      width: 300,
      fixed: 'right',
      render: row => (
        <div class="flex-center gap-2">
          <NButton size="small" onClick={() => showDetail(row.id)}>{$t('imageTools.detail')}</NButton>
          <NButton size="small" onClick={() => copyUrl(row.url)}>{$t('imageTools.copy')}</NButton>
          {canEdit.value ? <NButton size="small" disabled={deleting.value} onClick={() => openEdit(row)}>{$t('common.edit')}</NButton> : null}
          {canDelete.value ? (
            <NPopconfirm onPositiveClick={() => remove([row.id])}>
              {{
                default: () => $t('imageTools.deleteHint'),
                trigger: () => <NButton size="small" type="error" ghost disabled={deleting.value}>{$t('common.delete')}</NButton>
              }}
            </NPopconfirm>
          ) : null}
        </div>
      )
    }
  ]
});

watch(data, () => { selected.value = []; });

function formatSize(size: number) {
  return size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} KB` : `${(size / 1024 / 1024).toFixed(2)} MB`;
}

async function remove(ids: string[]) {
  if (deleting.value || !ids.length) return;
  deleting.value = true;
  try {
    const { error } = await fetchDeleteImages([...ids]);
    if (error) return;
    selected.value = [];
    if (detail.value && ids.includes(detail.value.id)) detail.value = null;
    window.$message?.success($t('common.deleteSuccess'));
    const page = pagination.page ?? 1;
    await getDataByPage(data.value.length <= ids.length ? Math.max(1, page - 1) : page);
  } finally {
    deleting.value = false;
  }
}

function openEdit(image: UploadedImage) {
  editing.value = image;
  editName.value = image.name;
}

async function saveName() {
  const name = editName.value.trim();
  if (!editing.value || saving.value) return;
  if (!name || /[/\\]/.test(name) || [...name].some(character => character.charCodeAt(0) < 32)) {
    window.$message?.error($t('imageTools.invalidName'));
    return;
  }

  saving.value = true;
  try {
    const { data: updated, error } = await fetchUpdateImage(editing.value.id, name);
    if (error || !updated) return;
    if (detail.value?.id === updated.id) detail.value = updated;
    editing.value = null;
    window.$message?.success($t('common.updateSuccess'));
    await getData();
  } finally {
    saving.value = false;
  }
}

async function showDetail(id: string) {
  const version = ++detailVersion;
  detailLoading.value = true;
  try {
    const { data: image, error } = await fetchUploadedImage(id);
    if (!error && image && version === detailVersion) detail.value = image;
  } finally {
    if (version === detailVersion) detailLoading.value = false;
  }
}

async function copyUrl(url: string) {
  try {
    await navigator.clipboard.writeText(new URL(imageSrc(url), window.location.origin).href);
    window.$message?.success($t('imageTools.copied'));
  } catch {
    window.$message?.error($t('imageTools.copyFailed'));
  }
}

defineExpose({ refresh: () => getDataByPage(1) });
</script>

<template>
  <div class="min-h-0 flex-col-stretch gap-16px sm:flex-1-hidden">
    <ImageSearch v-model:model="query" v-model:time-range="timeRange" @search="getDataByPage(1)" />

    <NCard :title="$t('imageTools.library')" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <template #header-extra>
        <TableHeaderOperation v-model:columns="columnChecks" :loading="loading" @refresh="getData">
          <NButton v-if="hasAuth('B_SYSTEM_UPLOAD_CREATE')" type="primary" size="small" @click="emit('add')">
            {{ $t('imageTools.add') }}
          </NButton>
          <NPopconfirm v-if="canDelete" @positive-click="remove(selected)">
            <template #trigger>
              <NButton type="error" ghost size="small" :disabled="!selected.length || deleting" :loading="deleting">
                {{ $t('common.batchDelete') }}
              </NButton>
            </template>
            {{ $t('imageTools.deleteHint') }}
          </NPopconfirm>
        </TableHeaderOperation>
      </template>

      <NDataTable
        v-model:checked-row-keys="selected"
        :columns="columns"
        :data="data"
        size="small"
        :flex-height="!appStore.isMobile"
        :scroll-x="scrollX"
        :loading="loading"
        remote
        :row-key="row => row.id"
        :pagination="mobilePagination"
        class="sm:h-full"
      />

      <NModal
        :show="Boolean(editing)"
        preset="card"
        :title="$t('common.edit')"
        class="w-120 max-w-95vw"
        :mask-closable="!saving"
        :close-on-esc="!saving"
        @update:show="
          show => {
            if (!show && !saving) editing = null;
          }
        "
      >
        <NForm @submit.prevent="saveName">
          <NFormItem :label="$t('imageTools.name')" required>
            <NInput v-model:value="editName" :maxlength="255" :disabled="saving" />
          </NFormItem>
          <p class="mb-4 text-gray-500">{{ $t('imageTools.renameHint') }}</p>
          <NButton type="primary" attr-type="submit" :loading="saving">{{ $t('common.confirm') }}</NButton>
        </NForm>
      </NModal>

      <NModal
        :show="Boolean(detail)"
        preset="card"
        :title="$t('imageTools.detail')"
        class="w-160 max-w-95vw"
        @update:show="
          show => {
            if (!show) detail = null;
          }
        "
      >
        <NSpace v-if="detail" vertical :size="16">
          <ImagePreview :value="detail.url" :width="240" :height="180" />
          <NDescriptions :column="1" bordered label-placement="left">
            <NDescriptionsItem :label="$t('imageTools.name')">{{ detail.name }}</NDescriptionsItem>
            <NDescriptionsItem :label="$t('imageTools.format')">{{ detail.mediaType }}</NDescriptionsItem>
            <NDescriptionsItem :label="$t('imageTools.fileSize')">{{ formatSize(detail.size) }}</NDescriptionsItem>
            <NDescriptionsItem :label="$t('imageTools.dimensions')">
              {{ detail.width }} × {{ detail.height }}
            </NDescriptionsItem>
            <NDescriptionsItem :label="$t('imageTools.uploader')">{{ detail.uploader || '—' }}</NDescriptionsItem>
            <NDescriptionsItem :label="$t('imageTools.uploadTime')">{{ detail.fmtCreatedAt }}</NDescriptionsItem>
            <NDescriptionsItem :label="$t('imageTools.updateTime')">{{ detail.fmtUpdatedAt }}</NDescriptionsItem>
          </NDescriptions>
          <NInput :value="imageSrc(detail.url)" readonly />
          <NButton @click="copyUrl(detail.url)">{{ $t('imageTools.copy') }}</NButton>
        </NSpace>
      </NModal>
    </NCard>
  </div>
</template>
