import { flushPromises, mount } from '@vue/test-utils';
import * as naive from 'naive-ui';
import { afterEach, expect, it, vi } from 'vitest';
import { fetchGetWeighingTicket, fetchSettlementRateOptions } from '@/service/api';
import Drawer from '../weighing-ticket-operate-drawer.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api/upload', () => ({ fetchUploadImage: vi.fn(), fetchUploadOptions: vi.fn() }));
vi.mock('@/service/api', () => ({
  fetchAddWeighingTicket: vi.fn(),
  fetchGetWeighingTicket: vi.fn(),
  fetchSettlementPreview: vi.fn(),
  fetchSettlementRateOptions: vi.fn(),
  fetchUpdateWeighingTicket: vi.fn(),
  fetchSettlementOrderOptions: vi.fn()
}));
afterEach(() => {
  document.body.innerHTML = '';
  vi.clearAllMocks();
});

it('opens the add drawer with actual Naive UI controls and survives failed rate loading', async () => {
  vi.mocked(fetchSettlementRateOptions).mockResolvedValue({ data: [], error: null } as never);
  const errors: unknown[] = [];
  const wrapper = mount(Drawer, {
    attachTo: document.body,
    props: { operateType: 'add', visible: false },
    global: {
      stubs: { ImageUpload: true, ImagePreview: true },
      plugins: [
        naive.create({
          components: [
            naive.NDrawer,
            naive.NDrawerContent,
            naive.NSpin,
            naive.NAlert,
            naive.NForm,
            naive.NFormItem,
            naive.NInput,
            naive.NDatePicker,
            naive.NSelect,
            naive.NSpace,
            naive.NText,
            naive.NButton,
            naive.NDivider,
            naive.NCard,
            naive.NDescriptions,
            naive.NDescriptionsItem,
            naive.NInputNumber,
            naive.NTable
          ]
        })
      ],
      config: {
        errorHandler: error => {
          errors.push(error);
        }
      }
    }
  });
  try {
    await wrapper.setProps({ visible: true });
    await flushPromises();
    expect(document.body.textContent).toContain('page.weighbridge_settlement.weighing_ticket.addWeighingTicket');
    expect(document.querySelector('.n-input')).not.toBeNull();
    expect(errors).toEqual([]);
    const datePicker = wrapper.findComponent(naive.NDatePicker);
    expect(datePicker.props('formattedValue')).toBeNull();
    datePicker.vm.$emit('update:formattedValue', '2026-11-01');
    await flushPromises();
    expect(datePicker.props('formattedValue')).toBe('2026-11-01');
    datePicker.vm.$emit('update:formattedValue', null);
    await flushPromises();
    expect(datePicker.props('formattedValue')).toBeNull();
    expect(errors).toEqual([]);
    await wrapper.setProps({ visible: false });
    await flushPromises();
    vi.mocked(fetchSettlementRateOptions).mockResolvedValue({
      data: null,
      error: new Error('rate lookup failed')
    } as never);
    vi.mocked(fetchGetWeighingTicket).mockResolvedValue({ data: null, error: null } as never);
    // Reopening the same draft intentionally reuses it; a different record starts a new load.
    await wrapper.setProps({ visible: true, operateType: 'edit', rowData: { id: 'other-ticket' } as never });
    await flushPromises();
    expect(document.body.textContent).toContain('page.weighbridge_settlement.settlement.loadFailed');
    expect(errors).toEqual([]);
  } finally {
    wrapper.unmount();
  }
});
