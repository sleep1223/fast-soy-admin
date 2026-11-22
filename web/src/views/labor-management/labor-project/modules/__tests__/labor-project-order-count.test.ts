import { flushPromises, mount } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import { fetchGetOrderList } from '@/service/api';
import OrderCount from '../labor-project-order-count.vue';
import { fetchMatchingOrdersForProjects, summarizeOrders } from '../matching-orders';

vi.mock('@/locales', () => ({ $t: (key: string) => key }));
vi.mock('@/service/api', () => ({ fetchGetOrderList: vi.fn() }));
const stubs = {
  NSpin: { template: '<span>loading</span>' },
  NButton: { emits: ['click'], template: '<button @click="$emit(\'click\')"><slot /></button>' }
};

it('loads summaries for multiple projects in one request and groups exact matches', async () => {
  vi.mocked(fetchGetOrderList).mockResolvedValueOnce({
    data: {
      records: [
        { partNo: 'P1', name: 'A' },
        { partNo: 'P10', name: 'B' }
      ],
      total: 2
    },
    error: null
  } as never);
  const result = await fetchMatchingOrdersForProjects(['P1', 'P10', 'P2'], () => true);
  expect(fetchGetOrderList).toHaveBeenCalledWith({ current: 1, size: 1000, partNos: ['P1', 'P10', 'P2'] });
  expect(result?.get('P1')).toHaveLength(1);
  expect(result?.get('P10')).toHaveLength(1);
  expect(result?.get('P2')).toHaveLength(0);
  vi.clearAllMocks();
});

it('summarizes process routes without dropping orders', () => {
  const orders = [
    { processRoute: ' 切割 ', customer: '客户甲' },
    { processRoute: '切割', customer: '客户乙' },
    { processRoute: '焊接', customer: '客户甲' },
    { processRoute: null, customer: '' }
  ] as Api.OrderManagementManage.Order[];
  expect(summarizeOrders(orders)).toEqual({
    count: 4,
    name: { value: null, variants: [null], inconsistent: false },
    processRoute: { value: '切割', variants: ['切割', '焊接', null], inconsistent: true }
  });
});

it('shows one value for matching fields and detects missing or different values', () => {
  const same = summarizeOrders([
    { name: '工件A', processRoute: ' 喷漆 ' },
    { name: '工件A', processRoute: '喷漆' }
  ] as Api.OrderManagementManage.Order[]);
  expect(same.name).toEqual({ value: '工件A', variants: ['工件A'], inconsistent: false });
  expect(same.processRoute).toEqual({ value: '喷漆', variants: ['喷漆'], inconsistent: false });
  const conflict = summarizeOrders([
    { name: '工件A', processRoute: null },
    { name: '工件B', processRoute: '喷漆' }
  ] as Api.OrderManagementManage.Order[]);
  expect(conflict.name.inconsistent).toBe(true);
  expect(conflict.processRoute.variants).toEqual([null, '喷漆']);
  expect(conflict.processRoute.inconsistent).toBe(true);
  expect(summarizeOrders([]).name).toEqual({ value: null, variants: [], inconsistent: false });
});

it('counts exact matches over all pages', async () => {
  vi.mocked(fetchGetOrderList)
    .mockResolvedValueOnce({ data: { records: [{ partNo: 'P1' }, { partNo: 'P1' }], total: 3 }, error: null } as never)
    .mockResolvedValueOnce({ data: { records: [{ partNo: 'P1' }], total: 3 }, error: null } as never);
  const wrapper = mount(OrderCount, { props: { partNo: 'P1' }, global: { stubs } });
  await flushPromises();
  expect(wrapper.text()).toBe('3');
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
