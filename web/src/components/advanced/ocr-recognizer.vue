<script setup lang="ts">
import { computed, onBeforeUnmount, ref, shallowRef, watch } from 'vue';
import { fetchOcrRecognize } from '@/service/api/ocr';
import { $t } from '@/locales';

defineOptions({ name: 'OcrRecognizer' });

const props = withDefaults(
  defineProps<{
    value?: Api.Ocr.Result | null;
    maxSizeMb?: number;
    disabled?: boolean;
    confidenceThreshold?: number;
    showBoxes?: boolean;
    autoRecognize?: boolean;
  }>(),
  {
    value: null,
    maxSizeMb: 10,
    disabled: false,
    confidenceThreshold: 0.9,
    showBoxes: true,
    autoRecognize: false
  }
);

const emit = defineEmits<{
  'update:value': [value: Api.Ocr.Result | null];
  recognized: [value: Api.Ocr.Result];
  error: [message: string];
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = shallowRef<File | null>(null);
const previewUrl = ref('');
const naturalWidth = ref(0);
const naturalHeight = ref(0);
const result = shallowRef<Api.Ocr.Result | null>(null);
const resultText = ref('');
const loading = ref(false);
const errorMessage = ref('');
let controller: AbortController | null = null;
let alive = true;

const imageWidth = computed(() => result.value?.width || naturalWidth.value);
const imageHeight = computed(() => result.value?.height || naturalHeight.value);
const lowConfidenceCount = computed(
  () => result.value?.items.filter(item => item.confidence < props.confidenceThreshold).length ?? 0
);
const boxes = computed(() => {
  if (!props.showBoxes || !result.value || !imageWidth.value || !imageHeight.value) return [];
  return result.value.items.flatMap((item, index) => {
    if (!item.box.length) return [];
    const xs = item.box.map(point => point[0]);
    const ys = item.box.map(point => point[1]);
    const left = (Math.min(...xs) / imageWidth.value) * 100;
    const top = (Math.min(...ys) / imageHeight.value) * 100;
    const width = ((Math.max(...xs) - Math.min(...xs)) / imageWidth.value) * 100;
    const height = ((Math.max(...ys) - Math.min(...ys)) / imageHeight.value) * 100;
    return [
      {
        key: index,
        low: item.confidence < props.confidenceThreshold,
        style: {
          left: `${left}%`,
          top: `${top}%`,
          width: `${width}%`,
          height: `${height}%`
        }
      }
    ];
  });
});

const extensions: Record<string, string> = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/gif': 'gif',
  'image/webp': 'webp'
};

function revokePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = '';
}

function reportError(message: string) {
  errorMessage.value = message;
  emit('error', message);
}

function normalizeClipboardFile(file: File): File {
  if (file.name.includes('.') || !extensions[file.type]) return file;
  return new File([file], `${file.name || 'image'}.${extensions[file.type]}`, {
    type: file.type,
    lastModified: file.lastModified
  });
}

function validFile(file: File) {
  const typeOk = Object.hasOwn(extensions, file.type) || /\.(jpe?g|png|gif|webp)$/i.test(file.name);
  if (!typeOk || !file.size || file.size > props.maxSizeMb * 1024 * 1024) {
    reportError($t('ocrTools.invalid', { size: props.maxSizeMb }));
    return false;
  }
  return true;
}

function selectFile(file: File) {
  if (props.disabled || loading.value) return;
  const normalized = normalizeClipboardFile(file);
  if (!validFile(normalized)) return;
  controller?.abort();
  revokePreview();
  result.value = null;
  resultText.value = '';
  naturalWidth.value = 0;
  naturalHeight.value = 0;
  errorMessage.value = '';
  selectedFile.value = normalized;
  previewUrl.value = URL.createObjectURL(normalized);
  emit('update:value', null);
  if (props.autoRecognize) void recognize();
}

function openPicker() {
  if (props.disabled || loading.value) return;
  fileInput.value?.click();
}

function onFileInput(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (file) selectFile(file);
}

function firstImageFile(list: FileList | null | undefined) {
  return Array.from(list ?? []).find(file => file.type.startsWith('image/')) ?? null;
}

function onDrop(event: DragEvent) {
  const transfer = event.dataTransfer;
  let file = firstImageFile(transfer?.files);
  if (!file) {
    file =
      Array.from(transfer?.items ?? []).flatMap(item => {
        const dropped = item.kind === 'file' ? item.getAsFile() : null;
        return dropped ? [dropped] : [];
      })[0] ?? null;
  }
  if (!file) {
    reportError($t('ocrTools.dropUnavailable'));
    return;
  }
  selectFile(file);
}

function onPaste(event: ClipboardEvent) {
  const file = firstImageFile(event.clipboardData?.files);
  if (!file) {
    reportError($t('ocrTools.dropUnavailable'));
    return;
  }
  selectFile(file);
}

async function recognize() {
  if (props.disabled || loading.value || !selectedFile.value) return;
  controller?.abort();
  const current = new AbortController();
  controller = current;
  loading.value = true;
  errorMessage.value = '';
  try {
    const { data, error } = await fetchOcrRecognize(selectedFile.value, { useCls: true }, current.signal);
    if (!alive || current.signal.aborted) return;
    if (error || !data) {
      reportError($t('ocrTools.failed'));
      return;
    }
    result.value = data;
    resultText.value = data.text;
    emit('recognized', data);
    emit('update:value', data);
  } catch {
    if (alive && !current.signal.aborted) reportError($t('ocrTools.failed'));
  } finally {
    if (alive && controller === current) loading.value = false;
  }
}

function onTextChange(value: string) {
  resultText.value = value;
  if (!result.value) return;
  const next = { ...result.value, text: value };
  result.value = next;
  emit('update:value', next);
}

function clear() {
  controller?.abort();
  controller = null;
  loading.value = false;
  selectedFile.value = null;
  result.value = null;
  resultText.value = '';
  naturalWidth.value = 0;
  naturalHeight.value = 0;
  errorMessage.value = '';
  revokePreview();
  emit('update:value', null);
}

function onImageLoad(event: Event) {
  const image = event.target as HTMLImageElement;
  naturalWidth.value = image.naturalWidth;
  naturalHeight.value = image.naturalHeight;
}

watch(
  () => props.value,
  value => {
    if (value === result.value) return;
    result.value = value ?? null;
    resultText.value = value?.text ?? '';
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  alive = false;
  controller?.abort();
  revokePreview();
});

defineExpose({ recognize, clear });
</script>

<template>
  <div class="min-w-0 flex-col gap-12px">
    <input ref="fileInput" type="file" accept=".jpg,.jpeg,.png,.gif,.webp" class="hidden" @change="onFileInput" />
    <div
      class="cursor-pointer border border-dashed border-gray-300 rounded-8px p-16px text-center transition-colors hover:border-primary"
      :class="{ 'pointer-events-none opacity-60': disabled }"
      role="button"
      tabindex="0"
      :aria-label="$t('ocrTools.select')"
      @click="openPicker"
      @keydown.enter.prevent="openPicker"
      @dragover.prevent
      @drop.prevent="onDrop"
      @paste.prevent="onPaste"
    >
      <div class="text-14px">{{ $t('ocrTools.dropHint') }}</div>
      <div class="mt-4px text-12px text-gray-400">{{ $t('ocrTools.tip') }}</div>
      <NButton class="mt-12px" size="small" :disabled="disabled || loading" @click.stop="openPicker">
        {{ selectedFile ? $t('ocrTools.replace') : $t('ocrTools.select') }}
      </NButton>
    </div>

    <NAlert v-if="errorMessage" type="error" :show-icon="true">{{ errorMessage }}</NAlert>

    <div v-if="previewUrl" class="w-full">
      <div class="relative inline-block max-w-full">
        <img
          :src="previewUrl"
          :alt="$t('ocrTools.imageAlt')"
          class="block max-w-full rounded-4px"
          @load="onImageLoad"
        />
        <span
          v-for="box in boxes"
          :key="box.key"
          class="pointer-events-none absolute border-2"
          :style="{ ...box.style, borderColor: box.low ? '#f0a020' : '#18a058' }"
        />
      </div>
      <NSpace class="mt-8px" align="center" wrap>
        <NButton type="primary" size="small" :loading="loading" :disabled="disabled" @click="recognize">
          {{ loading ? $t('ocrTools.recognizing') : $t('ocrTools.recognize') }}
        </NButton>
        <NButton size="small" :disabled="loading" @click="clear">{{ $t('ocrTools.clear') }}</NButton>
        <NText depth="3" class="text-12px">{{ $t('ocrTools.editHint') }}</NText>
      </NSpace>
    </div>

    <NSpin :show="loading">
      <div v-if="result" class="flex-col gap-8px">
        <NAlert v-if="result.truncated" type="warning" :show-icon="true">
          {{ $t('ocrTools.truncated', { count: result.items.length }) }}
        </NAlert>
        <div class="flex items-center gap-8px">
          <NText strong>{{ $t('ocrTools.result') }}</NText>
          <NTag v-if="lowConfidenceCount" type="warning" size="small">
            {{ $t('ocrTools.lowConfidence') }} ({{ lowConfidenceCount }})
          </NTag>
        </div>
        <NInput
          :value="resultText"
          type="textarea"
          :autosize="{ minRows: 4, maxRows: 12 }"
          :aria-label="$t('ocrTools.result')"
          @update:value="onTextChange"
        />
        <div class="max-h-240px overflow-auto">
          <div
            v-for="(item, index) in result.items"
            :key="`${index}-${item.text}`"
            class="flex items-center justify-between gap-8px border-b border-gray-100 py-4px last:border-0"
          >
            <span class="min-w-0 break-all text-13px">{{ item.text }}</span>
            <NTag :type="item.confidence < confidenceThreshold ? 'warning' : 'success'" size="small">
              {{ $t('ocrTools.confidence', { value: Math.round(item.confidence * 100) }) }}
            </NTag>
          </div>
        </div>
        <NText v-if="!result.items.length" depth="3">{{ $t('ocrTools.emptyText') }}</NText>
      </div>
    </NSpin>
  </div>
</template>
