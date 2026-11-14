declare namespace Api {
  namespace WorkTicketManagement {
    type Page<T> = Common.PaginatingQueryRecord<T>;
    type Id = string;

    type UnitOption = { id: Id; code: string; name: string };
    type WorkerOption = {
      id: Id;
      workerNo: string | null;
      name: string;
      productionUnitId: Id | null;
      enabled: boolean;
    };

    type MappingRow = {
      id: Id;
      orderId: Id;
      orderNo: string | null;
      partNo: string | null;
      name: string | null;
      productionUnitId: Id;
      productionUnitName: string;
      remark: string | null;
      createdAt: string;
    };

    type OrderCandidate = {
      id: Id;
      orderNo: string;
      partNo: string;
      name: string;
      netWeight: string;
      grossWeight: string | null;
      processRoute: string | null;
      quantity: number | null;
      receivedQuantity: number | null;
      mappingStatus: 'confirmed' | 'other_unit' | 'unconfirmed';
      mappedUnits: string[];
    };

    type MonthStatus = 'draft' | 'in_progress' | 'verified' | 'closed';

    type WorkMonthSummary = {
      id: Id;
      yearMonth: string;
      productionUnitId: Id;
      productionUnitName: string;
      status: MonthStatus;
      revision: number;
      rowCount: number;
      matchedRows: number;
      ambiguousRows: number;
      ticketCount: number;
      assignedTicketCount: number;
      timedTicketCount: number;
      anomalyCount: number;
      hasActualBatch: boolean;
      closedAt: string | null;
    };

    type StatusLog = {
      id: Id;
      fromStatus: MonthStatus | null;
      toStatus: MonthStatus;
      action: string;
      reason: string | null;
      createdBy: string | null;
      createdAt: string;
    };

    type ImportSourceType = 'plan' | 'actual';
    type MatchStatus = 'pending' | 'matched' | 'ambiguous' | 'missing' | 'unassigned' | 'other_unit' | 'invalid';
    type HandlingStatus = 'open' | 'resolved' | 'ignored';

    type ImportPreviewRow = {
      rowNumber: number;
      rawPartNo: string;
      normalizedPartNo: string;
      matchStatus: MatchStatus;
      matchSource: string;
      orderId: Id | null;
      orderNo: string | null;
      partNo: string | null;
      name: string | null;
      candidateCount: number;
      duplicateOfRowId: Id | null;
      note: string | null;
    };

    type ImportPreview = {
      sourceType: ImportSourceType;
      rows: ImportPreviewRow[];
      errors: string[];
      totalRows: number;
      invalidRows: number;
      duplicateRows: number;
      matchedRows: number;
      ambiguousRows: number;
      missingRows: number;
      truncated: boolean;
    };

    type ImportCommit = {
      batchId: Id;
      rowCount: number;
      invalidRows: number;
      duplicateRows: number;
      matchedRows: number;
      ambiguousRows: number;
      missingRows: number;
    };

    type ImportRow = {
      id: Id;
      batchId: Id;
      sourceType: ImportSourceType;
      rowNumber: number;
      rawPartNo: string;
      normalizedPartNo: string;
      orderId: Id | null;
      orderNo: string | null;
      partNo: string | null;
      name: string | null;
      matchStatus: MatchStatus;
      matchSource: string;
      handlingStatus: HandlingStatus;
      handlingNote: string | null;
      duplicateOfRowId: Id | null;
      sourceQuantity: string | null;
      note: string | null;
    };

    type ImportRowSearch = {
      workMonthId?: Id | null;
      sourceType?: ImportSourceType | null;
      matchStatus?: MatchStatus | null;
      handlingStatus?: HandlingStatus | null;
      batchId?: Id | null;
      keyword?: string | null;
      current: number;
      size: number;
    } & Partial<Common.PaginatingCommonParams>;

    type TicketStatus = 'active' | 'void';
    type ReconcileStatus = 'pending' | 'checked' | 'ignored';

    type Ticket = {
      id: Id;
      workMonthId: Id;
      yearMonth: string;
      productionUnitId: Id;
      productionUnitName: string;
      orderId: Id | null;
      orderNoSnapshot: string | null;
      partNoSnapshot: string | null;
      nameSnapshot: string | null;
      ticketCode: string | null;
      codeSource: string;
      codeConfidence: string | null;
      status: TicketStatus;
      reconcileStatus: ReconcileStatus;
      reconcileNote: string | null;
      assignmentCount: number;
      workerNames: string[];
      totalHours: string;
      hasTime: boolean;
      revision: number;
      remark: string | null;
      createdAt: string | null;
      updatedAt: string | null;
    };

    type TicketAssignment = {
      id: Id;
      workerId: Id;
      workerNo: string | null;
      workerName: string;
      workerEnabled: boolean;
      source: string;
      remark: string | null;
    };

    type TicketTimeEntry = {
      id: Id;
      workerId: Id;
      workerName: string;
      workDate: string;
      accountingMonth: string | null;
      hours: string;
      remark: string | null;
    };

    type TicketDetail = Ticket & {
      assignments: TicketAssignment[];
      timeEntries: TicketTimeEntry[];
    };

    type TicketSearch = {
      workMonthId?: Id | null;
      productionUnitId?: Id | null;
      yearMonthStart?: string | null;
      yearMonthEnd?: string | null;
      status?: TicketStatus | null;
      reconcileStatus?: ReconcileStatus | null;
      assignmentStatus?: 'all' | 'assigned' | 'unassigned';
      timeStatus?: 'all' | 'logged' | 'none';
      keyword?: string | null;
      orderNo?: string | null;
      partNo?: string | null;
      ticketCode?: string | null;
      current: number;
      size: number;
    } & Partial<Common.PaginatingCommonParams>;

    type CodePreviewRow = {
      orderId: Id | null;
      sourceImportRowId: Id | null;
      orderNo: string | null;
      partNo: string | null;
      name: string | null;
      previewCode: string | null;
      valid: boolean;
      error: string | null;
      conflictTicketId: Id | null;
      conflictCode: string | null;
    };

    type CodePreview = {
      configured: boolean;
      ruleName: string | null;
      rows: CodePreviewRow[];
      conflicts: number;
    };

    type CodeLookup = {
      code: string;
      normalized: string;
      valid: boolean;
      ticketId: Id | null;
      ticketCode: string | null;
      partNo: string | null;
      orderNo: string | null;
      ticketStatus: TicketStatus | null;
      workMonthId: Id | null;
      yearMonth: string | null;
      workMonthStatus: MonthStatus | null;
      otherMonthMatches: Array<{ ticketId: Id; ticketCode: string; yearMonth: string; status: string }>;
    };

    type OcrCandidate = {
      original: string;
      normalized: string;
      confidence: string | null;
      valid: boolean;
      duplicate: boolean;
      match: CodeLookup | null;
    };

    type TimeMatrixTicket = {
      id: Id;
      ticketCode: string | null;
      partNoSnapshot: string | null;
      orderNoSnapshot: string | null;
      nameSnapshot: string | null;
      revision: number;
    };

    type TimeMatrixEntry = {
      id: Id;
      ticketId: Id;
      workerId: Id;
      workDate: string;
      accountingMonth: string | null;
      hours: string;
    };

    type TimeMatrix = {
      tickets: TimeMatrixTicket[];
      workers: WorkerOption[];
      entries: TimeMatrixEntry[];
      totalHours: string;
      truncated: boolean;
    };

    type TimeEntry = {
      id: Id;
      ticketId: Id;
      ticketCode: string | null;
      partNoSnapshot: string | null;
      orderNoSnapshot: string | null;
      workerId: Id;
      workerName: string;
      workDate: string;
      accountingMonth: string | null;
      effectiveMonth: string;
      hours: string;
      remark: string | null;
      revision: number;
    };

    type TimeEntrySearch = {
      workMonthId?: Id | null;
      productionUnitId?: Id | null;
      workerId?: Id | null;
      ticketId?: Id | null;
      workDateStart?: string | null;
      workDateEnd?: string | null;
      accountingMonth?: string | null;
      current: number;
      size: number;
    } & Partial<Common.PaginatingCommonParams>;

    type ReconcileCategory =
      | 'plan_missing_actual'
      | 'actual_missing_plan'
      | 'actual_without_ticket'
      | 'ticket_without_order'
      | 'duplicate_code'
      | 'unassigned'
      | 'no_time'
      | 'ambiguous'
      | 'cross_month_duplicate';

    type ReconcileSummary = {
      workMonthId: Id;
      status: MonthStatus;
      counts: Record<ReconcileCategory, number>;
      blocking: number;
      warnings: number;
      hasActualBatch: boolean;
    };

    type ReconcileItem = {
      key: string;
      category: ReconcileCategory;
      severity: 'blocking' | 'warning';
      entityType: string;
      entityId: string | null;
      title: string;
      detail: string | null;
      actions: string[];
    };

    type ReportBasis = 'ticket_month' | 'work_date' | 'accounting_month';
    type ReportFilter = {
      yearMonthStart?: string | null;
      yearMonthEnd?: string | null;
      productionUnitId?: Id | null;
      workerId?: Id | null;
      includeVoid?: boolean;
      basis?: ReportBasis;
    };

    type MonthlyReportRow = {
      yearMonth: string;
      productionUnitId: Id;
      productionUnitName: string;
      ticketCount: number;
      assignedCount: number;
      unassignedCount: number;
      timedCount: number;
      noTimeCount: number;
      totalHours: string;
    };

    type MonthlyReport = { rows: MonthlyReportRow[]; totals: Record<string, string | number> };
    type WorkerHoursRow = {
      workerId: Id;
      workerName: string;
      productionUnitId: Id | null;
      productionUnitName: string | null;
      ticketCount: number;
      hours: string;
    };
    type WorkerHoursReport = { rows: WorkerHoursRow[]; totals: Record<string, string | number> };
    type WorkerDatesRow = { workDate: string; workerId: Id; workerName: string; hours: string };
    type WorkerDatesReport = { rows: WorkerDatesRow[] };
    type TicketStatusRow = { status: TicketStatus; reconcileStatus: ReconcileStatus; count: number };
    type TicketStatusReport = { rows: TicketStatusRow[] };
    type AnomalyRow = { category: ReconcileCategory; severity: 'blocking' | 'warning'; count: number };
    type AnomalyReport = { rows: AnomalyRow[]; totals: Record<string, number> };
  }
}
