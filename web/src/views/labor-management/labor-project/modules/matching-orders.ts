import { fetchGetOrderList } from '@/service/api';

export function summarizeOrders(orders: Api.OrderManagementManage.Order[]) {
  const distinct = (values: (string | null | undefined)[]) => [
    ...new Set(values.map(value => value?.trim()).filter((value): value is string => Boolean(value)))
  ];
  return {
    count: orders.length,
    processRoutes: distinct(orders.map(order => order.processRoute)),
    customers: distinct(orders.map(order => order.customer))
  };
}

/** The order search is fuzzy, so collect every page and retain exact project numbers. */
export async function fetchMatchingOrders(
  partNo: string,
  isCurrent: () => boolean
): Promise<Api.OrderManagementManage.Order[] | null> {
  const matches: Api.OrderManagementManage.Order[] = [];
  let page = 1;
  let received = 0;
  let total = 0;
  do {
    const { data, error } = await fetchGetOrderList({ current: page, size: 1000, partNo });
    if (!isCurrent()) return null;
    if (error || !data) throw new Error('Order lookup failed');
    matches.push(...data.records.filter(order => order.partNo === partNo));
    received += data.records.length;
    total = data.total;
    if (!data.records.length) break;
    page += 1;
  } while (received < total);
  return matches;
}
