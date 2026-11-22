import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { expect, it, vi } from 'vitest';
import { fetchAddLaborWorkHour, fetchGetLaborWorkHourList } from '@/service/api';
import WorkHours from '../labor-order-work-hours.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api', () => ({ fetchGetLaborWorkHourList: vi.fn(), fetchAddLaborWorkHour: vi.fn() }));
vi.mock('@/hooks/business/auth', () => ({ useAuth: () => ({ hasAuth: () => true }) }));

const Table = defineComponent({
  props: ['data'],
  setup: props => () => h('div', { 'data-records': JSON.stringify(props.data) })
});
const stubs = {
  NForm: { template: '<form><slot /></form>' },
  NFormItem: { template: '<div><slot /></div>' },
  NInput: {
    props: ['value'],
    emits: ['update:value'],
    template: '<input data-code :value="value" @input="$emit(\'update:value\', $event.target.value)" />'
  },
  NInputNumber: {
    props: ['value'],
    emits: ['update:value'],
    template:
      '<input data-hours type="number" :value="value" @input="$emit(\'update:value\', Number($event.target.value))" />'
  },
  NSpin: { template: '<div><slot /></div>' },
  NAlert: { template: '<div><slot /></div>' },
  NEmpty: { props: ['description'], template: '<div>{{ description }}</div>' },
  NButton: { template: '<button><slot /></button>' },
  NDataTable: Table
};

it('matches only the exact order number across all pages', async () => {
  vi.mocked(fetchGetLaborWorkHourList)
    .mockResolvedValueOnce({
      data: {
        records: [
          { id: '1', orderNo: 'O1', ticketCode: 'T1' },
          { id: '2', orderNo: 'O10', ticketCode: 'T2' }
        ],
        total: 3
      },
      error: null
    } as never)
    .mockResolvedValueOnce({
      data: { records: [{ id: '3', orderNo: 'O1', ticketCode: 'T3' }], total: 3 },
      error: null
    } as never);
  const wrapper = mount(WorkHours, { props: { orderNo: 'O1' }, global: { stubs } });
  await flushPromises();
  const data = JSON.parse(wrapper.find('[data-records]').attributes('data-records') ?? '[]');
  expect(data.map((item: { ticketCode: string }) => item.ticketCode)).toEqual(['T1', 'T3']);
  expect(fetchGetLaborWorkHourList).toHaveBeenCalledTimes(2);
  wrapper.unmount();
  vi.clearAllMocks();
});

it('creates an unassigned ticket for the expanded order and reloads its list', async () => {
  vi.mocked(fetchGetLaborWorkHourList)
    .mockResolvedValueOnce({ data: { records: [], total: 0 }, error: null } as never)
    .mockResolvedValueOnce({
      data: { records: [{ id: '1', orderNo: 'O1', ticketCode: 'T1', workHours: 2 }], total: 1 },
      error: null
    } as never);
  vi.mocked(fetchAddLaborWorkHour).mockResolvedValueOnce({ error: null } as never);
  const wrapper = mount(WorkHours, { props: { orderNo: 'O1' }, global: { stubs } });
  await flushPromises();
  await wrapper.get('[data-code]').setValue('  T1  ');
  await wrapper.get('[data-hours]').setValue('2');
  await wrapper.get('form').trigger('submit');
  await flushPromises();
  expect(fetchAddLaborWorkHour).toHaveBeenCalledWith({ orderNo: 'O1', ticketCode: 'T1', workHours: 2 });
  expect(fetchGetLaborWorkHourList).toHaveBeenCalledTimes(2);
  expect(JSON.parse(wrapper.get('[data-records]').attributes('data-records') ?? '[]')[0].ticketCode).toBe('T1');
  wrapper.unmount();
  vi.clearAllMocks();
});

it('does not submit incomplete data and keeps the input when creation fails', async () => {
  vi.mocked(fetchGetLaborWorkHourList).mockResolvedValueOnce({ data: { records: [], total: 0 }, error: null } as never);
  vi.mocked(fetchAddLaborWorkHour).mockResolvedValueOnce({ error: new Error('duplicate') } as never);
  const wrapper = mount(WorkHours, { props: { orderNo: 'O1' }, global: { stubs } });
  await flushPromises();
  await wrapper.get('form').trigger('submit');
  expect(fetchAddLaborWorkHour).not.toHaveBeenCalled();
  await wrapper.get('[data-code]').setValue('T1');
  await wrapper.get('[data-hours]').setValue('2');
  await wrapper.get('form').trigger('submit');
  await flushPromises();
  expect((wrapper.get('[data-code]').element as HTMLInputElement).value).toBe('T1');
  expect(fetchGetLaborWorkHourList).toHaveBeenCalledTimes(1);
  wrapper.unmount();
  vi.clearAllMocks();
});

it('hides the create form for a project marked as requiring no painting', async () => {
  vi.mocked(fetchGetLaborWorkHourList).mockResolvedValueOnce({ data: { records: [], total: 0 }, error: null } as never);
  const wrapper = mount(WorkHours, { props: { orderNo: 'O1', skipPainting: true }, global: { stubs } });
  await flushPromises();
  expect(wrapper.find('form').exists()).toBe(false);
  expect(fetchAddLaborWorkHour).not.toHaveBeenCalled();
  wrapper.unmount();
  vi.clearAllMocks();
});

it('distinguishes no matching tickets from a failed request', async () => {
  vi.mocked(fetchGetLaborWorkHourList).mockResolvedValueOnce({ data: { records: [], total: 0 }, error: null } as never);
  const wrapper = mount(WorkHours, { props: { orderNo: 'O1' }, global: { stubs } });
  await flushPromises();
  expect(wrapper.text()).toContain('noMatchedWorkHours');
  vi.mocked(fetchGetLaborWorkHourList).mockResolvedValueOnce({ data: null, error: new Error('failed') } as never);
  await wrapper.setProps({ orderNo: 'O2' });
  await flushPromises();
  expect(wrapper.text()).toContain('workHoursLoadFailed');
  wrapper.unmount();
  vi.clearAllMocks();
});
