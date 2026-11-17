declare namespace Api {
  namespace WeighbridgeSettlementManage {
    type CommonDeleteParams = { id: string };
    type CommonBatchDeleteParams = { ids: string[] };
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'current' | 'size'>;

    // ---- SettlementRate ----
    type SettlementRate = Common.CommonRecord<{
      processName: string;
      price: number;
      enabled: boolean | null;
    }>;

    type SettlementRateAddParams = {
      processName: string;
      price: number;
      enabled?: boolean | null;
    };

    type SettlementRateUpdateParams = { id?: string } & Partial<SettlementRateAddParams>;

    type SettlementRateSearchParams = CommonType.RecordNullable<
      {
        processName?: string;
        enabled?: boolean;
      } & CommonSearchParams
    >;

    type SettlementRateList = Common.PaginatingQueryRecord<SettlementRate>;

    // ---- WeighingTicket ----
    type WeighingTicket = Common.CommonRecord<{
      ticketNo: string;
      images: string[] | null;
      weighingDate: string;
      weight: number;
      process: string;
      price: number;
      totalAmount: number;
      isSettled: boolean | null;
      revision: number | null;
      rateId: string;
    }>;

    type LineInput = {
      id?: string;
      orderId: string | null;
      orderNo: string | null;
      partNo: string;
      name: string;
      netWeight: string | null;
      grossWeight?: string | null;
      quantity: number;
    };
    type WeighingLine = LineInput & {
      position: number;
      theoreticalWeight: string;
      allocatedWeight: string;
      amount: string;
      taxUnitPrice: string;
    };
    type TicketDetail = Omit<WeighingTicket, 'weight' | 'price' | 'totalAmount' | 'revision'> & {
      weight: string;
      price: string;
      totalAmount: string;
      revision: number;
      lines: WeighingLine[];
    };
    type RateOption = { id: string; processName: string; price: string };
    type OrderOption = {
      id: string;
      partNo: string;
      orderNo: string;
      name: string;
      netWeight: string | null;
      grossWeight?: string | null;
    };
    type Preview = { totalAmount: string; lines: WeighingLine[] };
    type WeighingTicketAddParams = {
      ticketNo: string;
      images?: string[] | null;
      weighingDate: string;
      weight: string;
      rateId?: string;
      lines: LineInput[];
    };
    type WeighingTicketUpdateParams = WeighingTicketAddParams & { id?: string; revision: number };

    type WeighingTicketSearchParams = CommonType.RecordNullable<
      {
        weighingDateStart?: string;
        weighingDateEnd?: string;
        ticketNo?: string;
        process?: string;
        isSettled?: boolean;
        rateId?: string;
      } & CommonSearchParams
    >;

    type WeighingTicketList = Common.PaginatingQueryRecord<WeighingTicket>;
  }
}
