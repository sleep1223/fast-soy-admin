import { request } from '../request';
import { createExcelFormData } from '@/utils/excel';
import type { ExcelDownload, ExcelImportOptions } from '@/utils/excel';

const base = '/business/work_ticket_management';

// ---- options / orders ----
export function fetchProductionUnitOptions() {
  return request<Api.WorkTicketManagement.UnitOption[]>({ url: `${base}/options/production_units` });
}

export function fetchWorkerOptions(productionUnitId?: string | null, includeDisabled = false) {
  return request<Api.WorkTicketManagement.WorkerOption[]>({
    url: `${base}/options/workers`,
    params: { productionUnitId: productionUnitId ?? undefined, includeDisabled }
  });
}

export function fetchOrderCandidates(data: {
  workMonthId: string;
  partNo: string;
  limit?: number;
  includeOtherUnits?: boolean;
  includePartial?: boolean;
}) {
  return request<Api.WorkTicketManagement.OrderCandidate[]>({ url: `${base}/orders/candidates`, method: 'post', data });
}

// ---- months ----
export function fetchOpenWorkMonth(data: { yearMonth: string; productionUnitId: string }) {
  return request<Api.WorkTicketManagement.WorkMonthSummary, 'json'>({
    url: `${base}/work_months/open`,
    method: 'post',
    data
  });
}

export function fetchWorkMonthSummary(id: string) {
  return request<Api.WorkTicketManagement.WorkMonthSummary>({ url: `${base}/work_months/${id}/summary` });
}

export function fetchWorkMonthStatusLogs(id: string) {
  return request<Api.WorkTicketManagement.StatusLog[]>({ url: `${base}/work_months/${id}/status-logs` });
}

export function fetchVerifyWorkMonth(id: string, data: { revision: number; reason?: string | null }) {
  return request<Api.WorkTicketManagement.WorkMonthSummary, 'json'>({
    url: `${base}/work_months/${id}/verify`,
    method: 'post',
    data
  });
}

export function fetchCloseWorkMonth(
  id: string,
  data: { revision: number; reason?: string | null; confirmWarnings?: boolean }
) {
  return request<Api.WorkTicketManagement.WorkMonthSummary, 'json'>({
    url: `${base}/work_months/${id}/close`,
    method: 'post',
    data
  });
}

export function fetchReopenWorkMonth(id: string, data: { revision: number; reason: string }) {
  return request<Api.WorkTicketManagement.WorkMonthSummary, 'json'>({
    url: `${base}/work_months/${id}/reopen`,
    method: 'post',
    data
  });
}

export function fetchExportWorkMonthWorkbook(id: string) {
  return request<ExcelDownload>({ url: `${base}/work_months/${id}/export`, method: 'post' });
}

// ---- imports ----
export function fetchImportPreview(
  file: File,
  workMonthId: string,
  sourceType: Api.WorkTicketManagement.ImportSourceType,
  options?: ExcelImportOptions
) {
  const data = createExcelFormData(file, options);
  data.append('workMonthId', workMonthId);
  data.append('sourceType', sourceType);
  return request<Api.WorkTicketManagement.ImportPreview>({
    url: `${base}/monthly_import_batches/preview`,
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportCommit(
  file: File,
  workMonthId: string,
  sourceType: Api.WorkTicketManagement.ImportSourceType,
  options?: ExcelImportOptions
) {
  const data = createExcelFormData(file, options);
  data.append('workMonthId', workMonthId);
  data.append('sourceType', sourceType);
  return request<Api.WorkTicketManagement.ImportCommit>({
    url: `${base}/monthly_import_batches/import`,
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchManualImport(data: {
  workMonthId: string;
  sourceType: Api.WorkTicketManagement.ImportSourceType;
  sourceName?: string | null;
  rows: Array<{ rawPartNo: string; sourceQuantity?: string | null }>;
}) {
  return request<Api.WorkTicketManagement.ImportCommit, 'json'>({
    url: `${base}/monthly_import_batches/manual`,
    method: 'post',
    data
  });
}

export function fetchVoidImportBatch(id: string, reason: string) {
  return request<null, 'json'>({ url: `${base}/monthly_import_batches/${id}/void`, method: 'post', data: { reason } });
}

export function fetchImportRows(data: Api.WorkTicketManagement.ImportRowSearch) {
  return request<Api.WorkTicketManagement.Page<Api.WorkTicketManagement.ImportRow>>({
    url: `${base}/monthly_import_rows/search`,
    method: 'post',
    data
  });
}

export function fetchUpdateImportRow(
  id: string,
  data: { rawPartNo?: string; sourceQuantity?: string | null; note?: string | null }
) {
  return request<Api.WorkTicketManagement.ImportRow, 'json'>({
    url: `${base}/monthly_import_rows/${id}`,
    method: 'patch',
    data
  });
}

export function fetchMatchImportRow(id: string, orderId: string, confirmMapping = true) {
  return request<Api.WorkTicketManagement.ImportRow, 'json'>({
    url: `${base}/monthly_import_rows/${id}/match`,
    method: 'post',
    data: { orderId, confirmMapping }
  });
}

export function fetchIgnoreImportRow(id: string, reason: string) {
  return request<Api.WorkTicketManagement.ImportRow, 'json'>({
    url: `${base}/monthly_import_rows/${id}/ignore`,
    method: 'post',
    data: { reason }
  });
}

export function fetchBatchMatchImportRows(workMonthId: string, ids?: string[]) {
  return request<Record<string, number>, 'json'>({
    url: `${base}/monthly_import_rows/batch-match`,
    method: 'post',
    data: { workMonthId, ids: ids?.length ? ids : null }
  });
}

// ---- tickets ----
export function fetchTickets(data: Api.WorkTicketManagement.TicketSearch) {
  return request<Api.WorkTicketManagement.Page<Api.WorkTicketManagement.Ticket>>({
    url: `${base}/work_tickets/search`,
    method: 'post',
    data
  });
}

export function fetchTicket(id: string) {
  return request<Api.WorkTicketManagement.TicketDetail>({ url: `${base}/work_tickets/${id}` });
}

export function fetchCreateTicket(data: {
  workMonthId: string;
  orderId?: string | null;
  sourceImportRowId?: string | null;
  partNoSnapshot?: string | null;
  nameSnapshot?: string | null;
  ticketCode?: string | null;
  codeSource?: string;
  remark?: string | null;
  workerIds?: string[];
  allowDisabledWorkers?: boolean;
  allowAddMapping?: boolean;
}) {
  return request<Api.WorkTicketManagement.TicketDetail, 'json'>({ url: `${base}/work_tickets`, method: 'post', data });
}

export function fetchUpdateTicket(id: string, data: Record<string, unknown>) {
  return request<Api.WorkTicketManagement.TicketDetail, 'json'>({
    url: `${base}/work_tickets/${id}`,
    method: 'patch',
    data
  });
}

export function fetchVoidTicket(id: string, revision: number, reason: string) {
  return request<Api.WorkTicketManagement.TicketDetail, 'json'>({
    url: `${base}/work_tickets/${id}/void`,
    method: 'post',
    data: { revision, reason }
  });
}

export function fetchAssignTicket(id: string, revision: number, workerIds: string[], allowDisabled = false) {
  return request<Api.WorkTicketManagement.TicketDetail, 'json'>({
    url: `${base}/work_tickets/${id}/assign`,
    method: 'post',
    data: { revision, workerIds, allowDisabled }
  });
}

export function fetchUnassignTicket(id: string, revision: number, workerId: string) {
  return request<Api.WorkTicketManagement.TicketDetail, 'json'>({
    url: `${base}/work_tickets/${id}/unassign`,
    method: 'post',
    data: { revision, workerId }
  });
}

export function fetchBatchAssignTickets(ticketIds: string[], workerIds: string[], allowDisabled = false) {
  return request<{ tickets: number; assignments: number }, 'json'>({
    url: `${base}/work_tickets/batch-assign`,
    method: 'post',
    data: { ticketIds, workerIds, allowDisabled }
  });
}

export function fetchReconcileTicket(
  id: string,
  revision: number,
  status: 'checked' | 'ignored',
  note?: string | null
) {
  return request<Api.WorkTicketManagement.TicketDetail, 'json'>({
    url: `${base}/work_tickets/${id}/reconcile`,
    method: 'post',
    data: { revision, status, note }
  });
}

export function fetchCodePreview(data: {
  workMonthId: string;
  ruleName?: string | null;
  items: Array<{ orderId?: string | null; sourceImportRowId?: string | null; sequence?: number }>;
}) {
  return request<Api.WorkTicketManagement.CodePreview, 'json'>({
    url: `${base}/work_tickets/code-preview`,
    method: 'post',
    data
  });
}

export function fetchCodeConfirm(data: {
  workMonthId: string;
  ruleName?: string | null;
  allowAddMapping?: boolean;
  items: Array<{ orderId?: string | null; sourceImportRowId?: string | null; sequence?: number; code?: string | null }>;
}) {
  return request<{ createdCount: number; skippedCount: number; ticketIds: string[]; conflicts: string[] }, 'json'>({
    url: `${base}/work_tickets/code-confirm`,
    method: 'post',
    data
  });
}

export function fetchPasteTicketCodes(items: Array<{ ticketId: string; revision: number; code: string }>) {
  return request<{ updatedCount: number; conflicts: string[] }, 'json'>({
    url: `${base}/work_tickets/codes/import`,
    method: 'post',
    data: { items }
  });
}

export function fetchCodeLookup(workMonthId: string, codes: string[], includeOtherMonths = true) {
  return request<Api.WorkTicketManagement.CodeLookup[], 'json'>({
    url: `${base}/work_tickets/code-lookup`,
    method: 'post',
    data: { workMonthId, codes, includeOtherMonths }
  });
}

export function fetchOcrCandidates(workMonthId: string, text: string, numericMode = true) {
  return request<Api.WorkTicketManagement.OcrCandidate[], 'json'>({
    url: `${base}/work_tickets/ocr-candidates`,
    method: 'post',
    data: { workMonthId, text, numericMode }
  });
}

export function fetchExportTickets(data: Api.WorkTicketManagement.TicketSearch) {
  return request<ExcelDownload>({ url: `${base}/work_tickets/export`, method: 'post', data });
}

// ---- time ----
export function fetchTimeMatrix(data: {
  workMonthId: string;
  workerIds?: string[] | null;
  ticketIds?: string[] | null;
  workDateStart?: string | null;
  workDateEnd?: string | null;
  ticketLimit?: number;
}) {
  return request<Api.WorkTicketManagement.TimeMatrix, 'json'>({
    url: `${base}/work_time_entries/matrix`,
    method: 'post',
    data
  });
}

export function fetchTimeBatchSave(data: {
  workMonthId: string;
  entries: Array<{
    ticketId: string;
    workerId: string;
    workDate: string;
    hours?: string | null;
    entryId?: string | null;
    accountingMonth?: string | null;
    revision: number;
  }>;
}) {
  return request<
    {
      savedCount: number;
      deletedCount: number;
      tickets: Array<{ ticketId: string; revision: number; totalHours: string }>;
    },
    'json'
  >({ url: `${base}/work_time_entries/batch-save`, method: 'post', data });
}

export function fetchTimeEntries(data: Api.WorkTicketManagement.TimeEntrySearch) {
  return request<Api.WorkTicketManagement.Page<Api.WorkTicketManagement.TimeEntry>>({
    url: `${base}/work_time_entries/search`,
    method: 'post',
    data
  });
}

export function fetchUpdateTimeEntry(
  id: string,
  data: { revision: number; hours: string; workDate: string; accountingMonth?: string | null; remark?: string | null }
) {
  return request<Api.WorkTicketManagement.TimeEntry, 'json'>({
    url: `${base}/work_time_entries/${id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteTimeEntry(id: string, revision: number) {
  return request<null, 'json'>({ url: `${base}/work_time_entries/${id}`, method: 'delete', data: { revision } });
}

export function fetchExportTimeEntries(data: Api.WorkTicketManagement.TimeEntrySearch) {
  return request<ExcelDownload>({ url: `${base}/work_time_entries/export`, method: 'post', data });
}

// ---- reconciliation ----
export function fetchReconciliationSummary(monthId: string) {
  return request<Api.WorkTicketManagement.ReconcileSummary>({
    url: `${base}/work_months/${monthId}/reconciliation/summary`
  });
}

export function fetchReconciliationItems(
  monthId: string,
  data: { category: Api.WorkTicketManagement.ReconcileCategory; current: number; size: number; keyword?: string | null }
) {
  return request<Api.WorkTicketManagement.Page<Api.WorkTicketManagement.ReconcileItem>>({
    url: `${base}/work_months/${monthId}/reconciliation/search`,
    method: 'post',
    data
  });
}

// ---- reports ----
export function fetchMonthlyReport(data: Api.WorkTicketManagement.ReportFilter) {
  return request<Api.WorkTicketManagement.MonthlyReport, 'json'>({
    url: `${base}/reports/monthly`,
    method: 'post',
    data
  });
}

export function fetchWorkerHoursReport(data: Api.WorkTicketManagement.ReportFilter) {
  return request<Api.WorkTicketManagement.WorkerHoursReport, 'json'>({
    url: `${base}/reports/worker-hours`,
    method: 'post',
    data
  });
}

export function fetchWorkerDatesReport(data: Api.WorkTicketManagement.ReportFilter) {
  return request<Api.WorkTicketManagement.WorkerDatesReport, 'json'>({
    url: `${base}/reports/worker-dates`,
    method: 'post',
    data
  });
}

export function fetchTicketStatusReport(data: Api.WorkTicketManagement.ReportFilter) {
  return request<Api.WorkTicketManagement.TicketStatusReport, 'json'>({
    url: `${base}/reports/ticket-status`,
    method: 'post',
    data
  });
}

export function fetchAnomalyReport(workMonthId: string) {
  return request<Api.WorkTicketManagement.AnomalyReport, 'json'>({
    url: `${base}/reports/anomalies`,
    method: 'post',
    data: { workMonthId }
  });
}

export function fetchExportReport(
  data: Api.WorkTicketManagement.ReportFilter & { reportType: string; workMonthId?: string | null }
) {
  return request<ExcelDownload>({ url: `${base}/reports/export`, method: 'post', data });
}
