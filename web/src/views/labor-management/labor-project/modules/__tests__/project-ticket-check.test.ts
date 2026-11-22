import { expect, it, vi } from 'vitest';
import { fetchGetLaborWorkHourList, fetchGetOrderList } from '@/service/api';
import { projectHasTickets } from '../matching-orders';

vi.mock('@/service/api', () => ({ fetchGetOrderList: vi.fn(), fetchGetLaborWorkHourList: vi.fn() }));

it('finds tickets using exact project and order numbers', async () => {
  vi.mocked(fetchGetOrderList).mockResolvedValueOnce({
    data: {
      records: [{ partNo: 'P1', orderNo: 'O1' }],
      total: 1
    },
    error: null
  } as never);
  vi.mocked(fetchGetLaborWorkHourList).mockResolvedValueOnce({
    data: { records: [{ orderNo: 'O1' }], total: 1 },
    error: null
  } as never);
  expect(await projectHasTickets('P1', () => true)).toBe(true);
  expect(fetchGetLaborWorkHourList).toHaveBeenCalledWith({ current: 1, size: 1, orderNos: ['O1'] });
  expect(fetchGetLaborWorkHourList).toHaveBeenCalledTimes(1);
  vi.clearAllMocks();
});

it('does not treat a failed lookup as an empty result', async () => {
  vi.mocked(fetchGetOrderList).mockResolvedValueOnce({
    data: { records: [{ partNo: 'P1', orderNo: 'O1' }], total: 1 },
    error: null
  } as never);
  vi.mocked(fetchGetLaborWorkHourList).mockResolvedValueOnce({ data: null, error: new Error('failed') } as never);
  await expect(projectHasTickets('P1', () => true)).rejects.toThrow();
  vi.clearAllMocks();
});
