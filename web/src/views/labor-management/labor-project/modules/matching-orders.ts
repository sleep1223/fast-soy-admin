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

/** Batch exact project-number searches while respecting the API's list and page limits. */
export async function fetchMatchingOrdersForProjects(
  partNos: string[],
  isCurrent: () => boolean
): Promise<Map<string, Api.OrderManagementManage.Order[]> | null> {
  const unique = [...new Set(partNos)];
  const grouped = new Map(unique.map(partNo => [partNo, [] as Api.OrderManagementManage.Order[]]));
  for (let offset = 0; offset < unique.length; offset += 100) {
    const batch = unique.slice(offset, offset + 100);
    const allowed = new Set(batch);
    let page = 1;
    let received = 0;
    let total = 0;
    do {
      const { data, error } = await fetchGetOrderList({ current: page, size: 1000, partNos: batch });
      if (!isCurrent()) return null;
      if (error || !data) throw new Error('Order lookup failed');
      for (const order of data.records) {
        if (!allowed.has(order.partNo)) throw new Error('Order lookup did not apply the exact project filter');
        grouped.get(order.partNo)?.push(order);
      }
      received += data.records.length;
      total = data.total;
      if (!data.records.length && received < total) throw new Error('Incomplete order lookup');
      if (!data.records.length) break;
      page += 1;
    } while (received < total);
  }
  return grouped;
}

export async function fetchMatchingOrders(
  partNo: string,
  isCurrent: () => boolean
): Promise<Api.OrderManagementManage.Order[] | null> {
  const grouped = await fetchMatchingOrdersForProjects([partNo], isCurrent);
  return grouped === null ? null : (grouped.get(partNo) ?? []);
}

/** Fail closed if either orders or tickets cannot be checked. */
export async function projectHasTickets(partNo: string, isCurrent: () => boolean): Promise<boolean | null> {
  const orders = await fetchMatchingOrders(partNo, isCurrent);
  if (!orders) return null;
  const orderNos = [...new Set(orders.map(order => order.orderNo))];
  for (let offset = 0; offset < orderNos.length; offset += 100) {
    const batch = orderNos.slice(offset, offset + 100);
    const { data, error } = await fetchGetLaborWorkHourList({ current: 1, size: 1, orderNos: batch });
    if (!isCurrent()) return null;
    if (error || !data) throw new Error('Ticket lookup failed');
    if (data.total > 0) {
      if (!data.records.length || !batch.includes(data.records[0].orderNo))
        throw new Error('Ticket lookup did not apply the exact order filter');
      return true;
    }
  }
  return false;
}
