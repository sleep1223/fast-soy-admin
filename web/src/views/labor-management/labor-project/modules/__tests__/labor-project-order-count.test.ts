import { flushPromises, mount } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import { fetchGetOrderList } from '@/service/api';
import OrderCount from '../labor-project-order-count.vue';
import { summarizeOrders } from '../matching-orders';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api', () => ({ fetchGetOrderList: vi.fn() }));
const stubs = {
  NSpin: { template: '<span>loading</span>' },
  NButton: { emits: ['click'], template: '<button @click="$emit(\'click\')"><slot /></button>' }
};

it('deduplicates nonempty process routes and customers without dropping orders', () => {
  const orders = [
    { processRoute: ' 切割 ', customer: '客户甲' },
    { processRoute: '切割', customer: '客户乙' },
    { processRoute: '焊接', customer: '客户甲' },
    { processRoute: null, customer: '' }
  ] as Api.OrderManagementManage.Order[];
  expect(summarizeOrders(orders)).toEqual({
    count: 4,
    processRoutes: ['切割', '焊接'],
    customers: ['客户甲', '客户乙']
  });
});

it('counts exact matches over all pages', async () => {
  vi.mocked(fetchGetOrderList)
    .mockResolvedValueOnce({ data: { records: [{ partNo: 'P1' }, { partNo: 'P10' }], total: 3 }, error: null } as never)
    .mockResolvedValueOnce({ data: { records: [{ partNo: 'P1' }], total: 3 }, error: null } as never);
  const wrapper = mount(OrderCount, { props: { partNo: 'P1' }, global: { stubs } });
  await flushPromises();
  expect(wrapper.text()).toBe('2');
  wrapper.unmount();
  vi.clearAllMocks();
});

it('allows retry after an error and displays zero for no matches', async () => {
  vi.mocked(fetchGetOrderList)
    .mockResolvedValueOnce({ data: null, error: new Error('failed') } as never)
    .mockResolvedValueOnce({ data: { records: [], total: 0 }, error: null } as never);
  const wrapper = mount(OrderCount, { props: { partNo: 'P1' }, global: { stubs } });
  await flushPromises();
  expect(wrapper.text()).toContain('retryOrders');
  await wrapper.get('button').trigger('click');
  await flushPromises();
  expect(wrapper.text()).toBe('0');
  wrapper.unmount();
  vi.clearAllMocks();
});
