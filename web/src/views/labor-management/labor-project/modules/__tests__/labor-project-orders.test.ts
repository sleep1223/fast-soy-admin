import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { expect, it, vi } from 'vitest';
import { fetchGetOrderList } from '@/service/api';
import ProjectOrders from '../labor-project-orders.vue';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api', () => ({ fetchGetOrderList: vi.fn() }));
vi.mock('@/hooks/business/auth', () => ({ useAuth: () => ({ hasAuth: () => false }) }));

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

it('loads exact project matches across pages', async () => {
  vi.mocked(fetchGetOrderList)
    .mockResolvedValueOnce({
      data: {
        records: [
          { id: '1', partNo: 'P1', orderNo: 'O1' },
          { id: '2', partNo: 'P1', orderNo: 'O2' }
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
  expect(data.map((item: { orderNo: string }) => item.orderNo)).toEqual(['O1', 'O2', 'O3']);
  expect(fetchGetOrderList).toHaveBeenNthCalledWith(1, { current: 1, size: 1000, partNos: ['P1'] });
  expect(fetchGetOrderList).toHaveBeenCalledTimes(2);
  expect(wrapper.emitted('loaded')?.[0]?.[0]).toHaveLength(3);
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
