declare namespace Api {
  namespace OrderManagementManage {
    type CommonDeleteParams = { id: string };
    type CommonBatchDeleteParams = { ids: string[] };
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'current' | 'size'>;

    // ---- Order ----
    type Order = Common.CommonRecord<{
      orderNo: string;
      partNo: string;
      name: string;
      netWeight: number | null;
      grossWeight?: number | null;
      unit: string | null;
      quantity: number | null;
      receivedQuantity: number | null;
      totalWeight: number | null;
      orderDueDate: string | null;
      completedDate: string | null;
      processRoute: string | null;
      customer: string | null;
    }>;

    type OrderAddParams = {
      orderNo: string;
      partNo: string;
      name: string;
      netWeight?: number | null;
      grossWeight?: number | null;
      unit?: string | null;
      quantity?: number | null;
      receivedQuantity?: number | null;
      totalWeight?: number | null;
      orderDueDate?: string | null;
      completedDate?: string | null;
      processRoute?: string | null;
      customer?: string | null;
    };

    type OrderUpdateParams = { id?: string } & Partial<OrderAddParams>;

    type OrderSearchParams = CommonType.RecordNullable<
      {
        orderNo?: string;
        partNo?: string;
        partNos?: string[];
        name?: string;
        unit?: string;
        orderDueDateStart?: string;
        orderDueDateEnd?: string;
        completedDateStart?: string;
        completedDateEnd?: string;
      } & CommonSearchParams
    >;

    type OrderList = Common.PaginatingQueryRecord<Order>;
  }
}
