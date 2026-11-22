import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { expect, it, vi } from 'vitest';
import { fetchGetOrderList } from '@/service/api';
import ProjectOrders from '../labor-project-orders.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api', () => ({ fetchGetOrderList: vi.fn() }));

const Table = defineComponent({
  props: ['data'],
  setup(props) {
    return () => h('div', { 'data-orders': JSON.stringify(props.data) });
  }
});
const stubs = {
  NSpin: { template: '<div><slot /></div>' },
  NAlert: { template: '<div><slot /></div>' },
  NEmpty: { props: ['description'], template: '<div>{{ description }}</div>' },
  NButton: { template: '<button><slot /></button>' },
  NDataTable: Table
};

it('matches exact project numbers across pages of fuzzy order results', async () => {
  vi.mocked(fetchGetOrderList)
    .mockResolvedValueOnce({
      data: {
        records: [
          { id: '1', partNo: 'P1', orderNo: 'O1' },
          { id: '2', partNo: 'P10', orderNo: 'O2' }
        ],
        total: 3
      },
      error: null
    } as never)
    .mockResolvedValueOnce({
      data: { records: [{ id: '3', partNo: 'P1', orderNo: 'O3' }], total: 3 },
      error: null
    } as never);
  const wrapper = mount(ProjectOrders, { props: { partNo: 'P1' }, global: { stubs } });
  await flushPromises();
  const data = JSON.parse(wrapper.find('[data-orders]').attributes('data-orders') ?? '[]');
  expect(data.map((item: { orderNo: string }) => item.orderNo)).toEqual(['O1', 'O3']);
  expect(fetchGetOrderList).toHaveBeenCalledTimes(2);
  wrapper.unmount();
  vi.clearAllMocks();
});

it('distinguishes an unmatched project from a failed order request', async () => {
  vi.mocked(fetchGetOrderList).mockResolvedValueOnce({ data: { records: [], total: 0 }, error: null } as never);
  const wrapper = mount(ProjectOrders, { props: { partNo: 'P1' }, global: { stubs } });
  await flushPromises();
  expect(wrapper.text()).toContain('noMatchedOrders');
  vi.mocked(fetchGetOrderList).mockResolvedValueOnce({ data: null, error: new Error('failed') } as never);
  await wrapper.setProps({ partNo: 'P2' });
  await flushPromises();
  expect(wrapper.text()).toContain('ordersLoadFailed');
  wrapper.unmount();
  vi.clearAllMocks();
});
