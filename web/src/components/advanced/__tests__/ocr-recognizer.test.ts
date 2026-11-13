import { defineComponent } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchOcrRecognize } from '@/service/api/ocr';
import OcrRecognizer from '../ocr-recognizer.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api/ocr', () => ({ fetchOcrRecognize: vi.fn() }));

const NButton = defineComponent({
  name: 'NButton',
  props: ['loading', 'disabled', 'type', 'size'],
  emits: ['click'],
  template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>'
});
const NAlert = defineComponent({
  name: 'NAlert',
  props: ['type', 'showIcon'],
  template: '<div class="alert"><slot /></div>'
});
const NSpace = defineComponent({ name: 'NSpace', template: '<div><slot /></div>' });
const NSpin = defineComponent({ name: 'NSpin', props: ['show'], template: '<div><slot /></div>' });
const NTag = defineComponent({ name: 'NTag', props: ['type', 'size'], template: '<span class="tag"><slot /></span>' });
const NText = defineComponent({ name: 'NText', props: ['depth', 'strong'], template: '<span><slot /></span>' });
const NInput = defineComponent({
  name: 'NInput',
  props: ['value', 'type', 'autosize'],
  emits: ['update:value'],
  template: '<textarea :value="value" @input="$emit(\'update:value\', $event.target.value)" />'
});

const components = { NButton, NAlert, NSpace, NSpin, NTag, NText, NInput };

function imageFile(name = 'ticket.png', type = 'image/png') {
  return new File(['image'], name, { type });
}

function result(text = '000123456', confidence = 0.98): Api.Ocr.Result {
  return {
    text,
    items: [
      {
        text,
        confidence,
        box: [
          [0, 0],
          [10, 0],
          [10, 10],
          [0, 10]
        ]
      }
    ],
    elapsedMs: 12,
    truncated: false,
    width: 100,
    height: 40
  };
}

function mountRecognizer(props: Record<string, unknown> = {}) {
  const wrapper = mount(OcrRecognizer, {
    props,
    global: { components }
  });
  return wrapper;
}

async function chooseFile(wrapper: ReturnType<typeof mountRecognizer>) {
  await wrapper.find('[role="button"]').trigger('drop', { dataTransfer: { files: [imageFile()] } });
  await flushPromises();
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test');
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
});

describe('ocr recognizer', () => {
  it('selects an image without uploading it and recognizes on demand', async () => {
    vi.mocked(fetchOcrRecognize).mockResolvedValue({ data: result(), error: null } as never);
    const wrapper = mountRecognizer();
    await chooseFile(wrapper);
    expect(wrapper.find('img').attributes('src')).toBe('blob:test');
    expect(fetchOcrRecognize).not.toHaveBeenCalled();

    const button = wrapper.findAll('button').find(item => item.text() === 'ocrTools.recognize');
    expect(button).toBeTruthy();
    await button!.trigger('click');
    await flushPromises();
    expect(fetchOcrRecognize).toHaveBeenCalledTimes(1);
    expect(wrapper.emitted('recognized')?.at(-1)?.[0]).toMatchObject({ text: '000123456' });
    expect(wrapper.emitted('update:value')?.at(-1)?.[0]).toMatchObject({ text: '000123456' });
    expect(wrapper.find('textarea').element.value).toBe('000123456');
  });

  it('marks low confidence and lets the user correct the text', async () => {
    vi.mocked(fetchOcrRecognize).mockResolvedValue({ data: result('OO0123456', 0.5), error: null } as never);
    const wrapper = mountRecognizer();
    await chooseFile(wrapper);
    await wrapper
      .findAll('button')
      .find(item => item.text() === 'ocrTools.recognize')!
      .trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('ocrTools.lowConfidence');
    await wrapper.find('textarea').setValue('000123456');
    expect(wrapper.emitted('update:value')?.at(-1)?.[0]).toMatchObject({ text: '000123456' });
  });

  it('rejects invalid or oversize files before any request', async () => {
    const wrapper = mountRecognizer({ maxSizeMb: 1 });
    const dropZone = wrapper.find('[role="button"]');
    await dropZone.trigger('drop', {
      dataTransfer: { files: [new File(['x'], 'bad.svg', { type: 'image/svg+xml' })] }
    });
    await flushPromises();
    expect(wrapper.text()).toContain('ocrTools.invalid');
    expect(fetchOcrRecognize).not.toHaveBeenCalled();

    await dropZone.trigger('drop', {
      dataTransfer: { files: [new File([new Uint8Array(1024 * 1024 + 1)], 'large.png', { type: 'image/png' })] }
    });
    await flushPromises();
    expect(wrapper.text()).toContain('ocrTools.invalid');
  });

  it('accepts a pasted screenshot and clears the preview', async () => {
    const wrapper = mountRecognizer();
    await wrapper.find('[role="button"]').trigger('paste', { clipboardData: { files: [imageFile('clipboard.png')] } });
    await flushPromises();
    expect(wrapper.find('img').attributes('src')).toBe('blob:test');

    await wrapper
      .findAll('button')
      .find(item => item.text() === 'ocrTools.clear')!
      .trigger('click');
    expect(wrapper.find('img').exists()).toBe(false);
    expect(wrapper.emitted('update:value')?.at(-1)).toEqual([null]);
  });
});
