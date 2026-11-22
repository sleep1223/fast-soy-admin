import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { expect, it, vi } from 'vitest';
import { fetchUpdateLaborProject } from '@/service/api';
import Drawer from '../labor-project-operate-drawer.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api', () => ({ fetchAddLaborProject: vi.fn(), fetchUpdateLaborProject: vi.fn() }));
vi.mock('@/hooks/common/form', () => ({
  useFormRules: () => ({ defaultRequiredRule: {} }),
  useNaiveForm: () => ({ formRef: null, validate: vi.fn().mockResolvedValue(undefined), restoreValidation: vi.fn() })
}));

const DatePicker = defineComponent({ props: ['value'], emits: ['update:value'], setup: () => () => h('div') });
const stubs = {
  NDrawer: { template: '<div><slot /></div>' },
  NDrawerContent: { template: '<div><slot /><slot name="footer" /></div>' },
  NForm: { template: '<div><slot /></div>' },
  NFormItem: { template: '<div><slot /></div>' },
  NInput: { template: '<input />' },
  NDatePicker: DatePicker,
  NSpace: { template: '<div><slot /></div>' },
  NButton: { emits: ['click'], template: '<button @click="$emit(\'click\')"><slot /></button>' }
};

it('saves a manually adjusted import time without overwriting the painting flag', async () => {
  vi.mocked(fetchUpdateLaborProject).mockResolvedValueOnce({ error: null } as never);
  const initial = Date.parse('2025-01-01T00:00:00Z');
  const changed = Date.parse('2026-04-05T12:30:00Z');
  const wrapper = mount(Drawer, {
    props: {
      operateType: 'edit',
      visible: false,
      rowData: { id: 'id1', partNo: 'P1', importedAt: initial, skipPainting: true } as never
    },
    global: { stubs }
  });
  await wrapper.setProps({ visible: true });
  expect(wrapper.getComponent(DatePicker).props('value')).toBe(initial);
  wrapper.getComponent(DatePicker).vm.$emit('update:value', changed);
  await wrapper.findAll('button')[1].trigger('click');
  await flushPromises();
  expect(fetchUpdateLaborProject).toHaveBeenCalledWith({
    id: 'id1',
    partNo: 'P1',
    importedAt: '2026-04-05T12:30:00.000Z'
  });
  wrapper.unmount();
  vi.clearAllMocks();
});
