declare namespace Api {
  namespace WorkTicketManagementManage {
    type CommonDeleteParams = { id: string };
    type CommonBatchDeleteParams = { ids: string[] };
    type CommonSearchParams = Pick<Common.PaginatingCommonParams, 'current' | 'size'>;

    // ---- ProductionUnit ----
    type ProductionUnit = Common.CommonRecord<{
      code: string;
      name: string;
      enabled: boolean | null;
      remark: string | null;
    }>;

    type ProductionUnitAddParams = {
      code: string;
      name: string;
      enabled?: boolean | null;
      remark?: string | null;
    };

    type ProductionUnitUpdateParams = { id?: string } & Partial<ProductionUnitAddParams>;

    type ProductionUnitSearchParams = CommonType.RecordNullable<
      {
        code?: string;
        name?: string;
        enabled?: boolean;
        remark?: string;
      } & CommonSearchParams
    >;

    type ProductionUnitList = Common.PaginatingQueryRecord<ProductionUnit>;

    // ---- Worker ----
    type Worker = Common.CommonRecord<{
      workerNo: string | null;
      name: string;
      enabled: boolean | null;
      remark: string | null;
      productionUnitId: string | null;
    }>;

    type WorkerAddParams = {
      workerNo?: string | null;
      name: string;
      enabled?: boolean | null;
      remark?: string | null;
      productionUnitId?: string | null;
    };

    type WorkerUpdateParams = { id?: string } & Partial<WorkerAddParams>;

    type WorkerSearchParams = CommonType.RecordNullable<
      {
        workerNo?: string;
        name?: string;
        enabled?: boolean;
        remark?: string;
        productionUnitId?: string;
      } & CommonSearchParams
    >;

    type WorkerList = Common.PaginatingQueryRecord<Worker>;

    // ---- OrderUnitMapping ----
    type OrderUnitMapping = Common.CommonRecord<{
      remark: string | null;
      orderId: string;
      productionUnitId: string;
    }>;

    type OrderUnitMappingAddParams = {
      remark?: string | null;
      orderId: string;
      productionUnitId: string;
    };

    type OrderUnitMappingUpdateParams = { id?: string } & Partial<OrderUnitMappingAddParams>;

    type OrderUnitMappingSearchParams = CommonType.RecordNullable<
      {
        remark?: string;
        orderId?: string;
        productionUnitId?: string;
      } & CommonSearchParams
    >;

    type OrderUnitMappingList = Common.PaginatingQueryRecord<OrderUnitMapping>;

    // ---- WorkMonth ----
    type WorkMonth = Common.CommonRecord<{
      yearMonth: string;
      status: string | null;
      remark: string | null;
      revision: number | null;
      closedAt: string | null;
      closedBy: string | null;
      reopenedAt: string | null;
      reopenCount: number | null;
      productionUnitId: string;
    }>;

    type WorkMonthAddParams = {
      yearMonth: string;
      status?: string | null;
      remark?: string | null;
      revision?: number | null;
      closedAt?: string | null;
      closedBy?: string | null;
      reopenedAt?: string | null;
      reopenCount?: number | null;
      productionUnitId: string;
    };

    type WorkMonthUpdateParams = { id?: string } & Partial<WorkMonthAddParams>;

    type WorkMonthSearchParams = CommonType.RecordNullable<
      {
        yearMonth?: string;
        status?: string;
        remark?: string;
        revision?: number;
        closedAtStart?: string;
        closedAtEnd?: string;
        closedBy?: string;
        reopenedAtStart?: string;
        reopenedAtEnd?: string;
        reopenCount?: number;
        productionUnitId?: string;
      } & CommonSearchParams
    >;

    type WorkMonthList = Common.PaginatingQueryRecord<WorkMonth>;

    // ---- MonthlyImportBatch ----
    type MonthlyImportBatch = Common.CommonRecord<{
      sourceType: string;
      status: string | null;
      sourceName: string | null;
      contentHash: string | null;
      rowCount: number | null;
      voidReason: string | null;
      voidedAt: string | null;
      voidedBy: string | null;
      remark: string | null;
      workMonthId: string;
    }>;

    type MonthlyImportBatchAddParams = {
      sourceType: string;
      status?: string | null;
      sourceName?: string | null;
      contentHash?: string | null;
      rowCount?: number | null;
      voidReason?: string | null;
      voidedAt?: string | null;
      voidedBy?: string | null;
      remark?: string | null;
      workMonthId: string;
    };

    type MonthlyImportBatchUpdateParams = { id?: string } & Partial<MonthlyImportBatchAddParams>;

    type MonthlyImportBatchSearchParams = CommonType.RecordNullable<
      {
        sourceType?: string;
        status?: string;
        sourceName?: string;
        contentHash?: string;
        rowCount?: number;
        voidReason?: string;
        voidedAtStart?: string;
        voidedAtEnd?: string;
        voidedBy?: string;
        remark?: string;
        workMonthId?: string;
      } & CommonSearchParams
    >;

    type MonthlyImportBatchList = Common.PaginatingQueryRecord<MonthlyImportBatch>;

    // ---- MonthlyImportRow ----
    type MonthlyImportRow = Common.CommonRecord<{
      rowNumber: number;
      rawPartNo: string;
      normalizedPartNo: string;
      matchStatus: string | null;
      matchSource: string | null;
      sourceQuantity: number | null;
      rawData: Record<string, any> | null;
      handlingStatus: string | null;
      handlingNote: string | null;
      handledAt: string | null;
      handledBy: string | null;
      note: string | null;
      batchId: string;
      orderId: string | null;
      duplicateOfRowId: string | null;
    }>;

    type MonthlyImportRowAddParams = {
      rowNumber: number;
      rawPartNo: string;
      normalizedPartNo: string;
      matchStatus?: string | null;
      matchSource?: string | null;
      sourceQuantity?: number | null;
      rawData?: Record<string, any> | null;
      handlingStatus?: string | null;
      handlingNote?: string | null;
      handledAt?: string | null;
      handledBy?: string | null;
      note?: string | null;
      batchId: string;
      orderId?: string | null;
      duplicateOfRowId?: string | null;
    };

    type MonthlyImportRowUpdateParams = { id?: string } & Partial<MonthlyImportRowAddParams>;

    type MonthlyImportRowSearchParams = CommonType.RecordNullable<
      {
        rowNumber?: number;
        rawPartNo?: string;
        normalizedPartNo?: string;
        matchStatus?: string;
        matchSource?: string;
        sourceQuantity?: number;
        handlingStatus?: string;
        handlingNote?: string;
        handledAtStart?: string;
        handledAtEnd?: string;
        handledBy?: string;
        note?: string;
        batchId?: string;
        orderId?: string;
        duplicateOfRowId?: string;
      } & CommonSearchParams
    >;

    type MonthlyImportRowList = Common.PaginatingQueryRecord<MonthlyImportRow>;

    // ---- WorkTicket ----
    type WorkTicket = Common.CommonRecord<{
      orderNoSnapshot: string | null;
      partNoSnapshot: string | null;
      nameSnapshot: string | null;
      ticketCode: string | null;
      ticketCodeKey: string | null;
      codeSource: string | null;
      codeRuleVersion: string | null;
      codeConfidence: number | null;
      status: string | null;
      reconcileStatus: string | null;
      reconcileNote: string | null;
      voidReason: string | null;
      voidedAt: string | null;
      voidedBy: string | null;
      remark: string | null;
      revision: number | null;
      workMonthId: string;
      orderId: string | null;
      sourceImportRowId: string | null;
    }>;

    type WorkTicketAddParams = {
      orderNoSnapshot?: string | null;
      partNoSnapshot?: string | null;
      nameSnapshot?: string | null;
      ticketCode?: string | null;
      ticketCodeKey?: string | null;
      codeSource?: string | null;
      codeRuleVersion?: string | null;
      codeConfidence?: number | null;
      status?: string | null;
      reconcileStatus?: string | null;
      reconcileNote?: string | null;
      voidReason?: string | null;
      voidedAt?: string | null;
      voidedBy?: string | null;
      remark?: string | null;
      revision?: number | null;
      workMonthId: string;
      orderId?: string | null;
      sourceImportRowId?: string | null;
    };

    type WorkTicketUpdateParams = { id?: string } & Partial<WorkTicketAddParams>;

    type WorkTicketSearchParams = CommonType.RecordNullable<
      {
        orderNoSnapshot?: string;
        partNoSnapshot?: string;
        nameSnapshot?: string;
        ticketCode?: string;
        ticketCodeKey?: string;
        codeSource?: string;
        codeRuleVersion?: string;
        codeConfidence?: number;
        status?: string;
        reconcileStatus?: string;
        reconcileNote?: string;
        voidReason?: string;
        voidedAtStart?: string;
        voidedAtEnd?: string;
        voidedBy?: string;
        remark?: string;
        revision?: number;
        workMonthId?: string;
        orderId?: string;
        sourceImportRowId?: string;
      } & CommonSearchParams
    >;

    type WorkTicketList = Common.PaginatingQueryRecord<WorkTicket>;

    // ---- WorkTicketAssignment ----
    type WorkTicketAssignment = Common.CommonRecord<{
      source: string | null;
      remark: string | null;
      ticketId: string;
      workerId: string;
    }>;

    type WorkTicketAssignmentAddParams = {
      source?: string | null;
      remark?: string | null;
      ticketId: string;
      workerId: string;
    };

    type WorkTicketAssignmentUpdateParams = { id?: string } & Partial<WorkTicketAssignmentAddParams>;

    type WorkTicketAssignmentSearchParams = CommonType.RecordNullable<
      {
        source?: string;
        remark?: string;
        ticketId?: string;
        workerId?: string;
      } & CommonSearchParams
    >;

    type WorkTicketAssignmentList = Common.PaginatingQueryRecord<WorkTicketAssignment>;

    // ---- WorkTimeEntry ----
    type WorkTimeEntry = Common.CommonRecord<{
      workDate: string;
      accountingMonth: string | null;
      hours: number;
      remark: string | null;
      assignmentId: string;
    }>;

    type WorkTimeEntryAddParams = {
      workDate: string;
      accountingMonth?: string | null;
      hours: number;
      remark?: string | null;
      assignmentId: string;
    };

    type WorkTimeEntryUpdateParams = { id?: string } & Partial<WorkTimeEntryAddParams>;

    type WorkTimeEntrySearchParams = CommonType.RecordNullable<
      {
        workDateStart?: string;
        workDateEnd?: string;
        accountingMonth?: string;
        hours?: number;
        remark?: string;
        assignmentId?: string;
      } & CommonSearchParams
    >;

    type WorkTimeEntryList = Common.PaginatingQueryRecord<WorkTimeEntry>;

    // ---- WorkMonthStatusLog ----
    type WorkMonthStatusLog = Common.CommonRecord<{
      fromStatus: string | null;
      toStatus: string;
      action: string;
      reason: string | null;
      summary: Record<string, any> | null;
      workMonthId: string;
    }>;

    type WorkMonthStatusLogAddParams = {
      fromStatus?: string | null;
      toStatus: string;
      action: string;
      reason?: string | null;
      summary?: Record<string, any> | null;
      workMonthId: string;
    };

    type WorkMonthStatusLogUpdateParams = { id?: string } & Partial<WorkMonthStatusLogAddParams>;

    type WorkMonthStatusLogSearchParams = CommonType.RecordNullable<
      {
        fromStatus?: string;
        toStatus?: string;
        action?: string;
        reason?: string;
        workMonthId?: string;
      } & CommonSearchParams
    >;

    type WorkMonthStatusLogList = Common.PaginatingQueryRecord<WorkMonthStatusLog>;
  }
}
