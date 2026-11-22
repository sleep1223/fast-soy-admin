import { fetchGetLaborWorkHourList, fetchGetOrderList } from '@/service/api';

export function summarizeOrders(orders: Api.OrderManagementManage.Order[]) {
  const summarizeField = (values: (string | null | undefined)[]) => {
    const variants = [...new Set(values.map(value => value?.trim() || null))];
    return {
      value: variants.find((value): value is string => value !== null) ?? null,
      variants,
      inconsistent: variants.length > 1
    };
  };
  return {
    count: orders.length,
    name: summarizeField(orders.map(order => order.name)),
    processRoute: summarizeField(orders.map(order => order.processRoute))
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
    if (!data.records.length && received < total) throw new Error('Incomplete order lookup');
    if (!data.records.length) break;
    page += 1;
  } while (received < total);
  return matches;
}

/** Fail closed if either orders or tickets cannot be checked. */
export async function projectHasTickets(partNo: string, isCurrent: () => boolean): Promise<boolean | null> {
  const orders = await fetchMatchingOrders(partNo, isCurrent);
  if (!orders) return null;
  for (const order of orders) {
    let page = 1;
    let received = 0;
    let total = 0;
    do {
      const { data, error } = await fetchGetLaborWorkHourList({ current: page, size: 1000, orderNo: order.orderNo });
      if (!isCurrent()) return null;
      if (error || !data) throw new Error('Ticket lookup failed');
      if (data.records.some(ticket => ticket.orderNo === order.orderNo)) return true;
      received += data.records.length;
      total = data.total;
      if (!data.records.length && received < total) throw new Error('Incomplete ticket lookup');
      if (!data.records.length) break;
      page += 1;
    } while (received < total);
  }
  return false;
}
