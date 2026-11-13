import { request } from '../request';
import { createExcelFormData } from '@/utils/excel';
import type { ExcelDownload, ExcelImportOptions, ExcelImportResult, ExcelPreview } from '@/utils/excel';

// ---- ProductionUnit ----
export function fetchGetProductionUnitList(data?: Api.WorkTicketManagementManage.ProductionUnitSearchParams) {
  return request<Api.WorkTicketManagementManage.ProductionUnitList>({
    url: '/business/work_ticket_management/production_units/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetProductionUnit(id: string) {
  return request<Api.WorkTicketManagementManage.ProductionUnit>({
    url: `/business/work_ticket_management/production_units/${id}`,
    method: 'get'
  });
}

export function fetchAddProductionUnit(data?: Api.WorkTicketManagementManage.ProductionUnitAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/production_units',
    method: 'post',
    data
  });
}

export function fetchUpdateProductionUnit(data?: Api.WorkTicketManagementManage.ProductionUnitUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/production_units/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteProductionUnit(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/production_units/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteProductionUnit(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/production_units',
    method: 'delete',
    data
  });
}

export function fetchExportProductionUnit(
  data?: Api.WorkTicketManagementManage.ProductionUnitSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/production_units/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchProductionUnitImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/production_units/import-template' });
}

export function fetchPreviewImportProductionUnit(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/production_units/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportProductionUnit(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/production_units/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- Worker ----
export function fetchGetWorkerList(data?: Api.WorkTicketManagementManage.WorkerSearchParams) {
  return request<Api.WorkTicketManagementManage.WorkerList>({
    url: '/business/work_ticket_management/workers/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetWorker(id: string) {
  return request<Api.WorkTicketManagementManage.Worker>({
    url: `/business/work_ticket_management/workers/${id}`,
    method: 'get'
  });
}

export function fetchAddWorker(data?: Api.WorkTicketManagementManage.WorkerAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/workers',
    method: 'post',
    data
  });
}

export function fetchUpdateWorker(data?: Api.WorkTicketManagementManage.WorkerUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/workers/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteWorker(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/workers/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteWorker(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/workers',
    method: 'delete',
    data
  });
}

export function fetchExportWorker(
  data?: Api.WorkTicketManagementManage.WorkerSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/workers/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchWorkerImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/workers/import-template' });
}

export function fetchPreviewImportWorker(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/workers/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorker(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/workers/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- OrderUnitMapping ----
export function fetchGetOrderUnitMappingList(data?: Api.WorkTicketManagementManage.OrderUnitMappingSearchParams) {
  return request<Api.WorkTicketManagementManage.OrderUnitMappingList>({
    url: '/business/work_ticket_management/order_unit_mappings/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetOrderUnitMapping(id: string) {
  return request<Api.WorkTicketManagementManage.OrderUnitMapping>({
    url: `/business/work_ticket_management/order_unit_mappings/${id}`,
    method: 'get'
  });
}

export function fetchAddOrderUnitMapping(data?: Api.WorkTicketManagementManage.OrderUnitMappingAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/order_unit_mappings',
    method: 'post',
    data
  });
}

export function fetchUpdateOrderUnitMapping(data?: Api.WorkTicketManagementManage.OrderUnitMappingUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/order_unit_mappings/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteOrderUnitMapping(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/order_unit_mappings/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteOrderUnitMapping(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/order_unit_mappings',
    method: 'delete',
    data
  });
}

export function fetchExportOrderUnitMapping(
  data?: Api.WorkTicketManagementManage.OrderUnitMappingSearchParams & { ids?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/order_unit_mappings/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchOrderUnitMappingImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/order_unit_mappings/import-template' });
}

export function fetchPreviewImportOrderUnitMapping(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/order_unit_mappings/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportOrderUnitMapping(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/order_unit_mappings/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- WorkMonth ----
export function fetchGetWorkMonthList(data?: Api.WorkTicketManagementManage.WorkMonthSearchParams) {
  return request<Api.WorkTicketManagementManage.WorkMonthList>({
    url: '/business/work_ticket_management/work_months/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetWorkMonth(id: string) {
  return request<Api.WorkTicketManagementManage.WorkMonth>({
    url: `/business/work_ticket_management/work_months/${id}`,
    method: 'get'
  });
}

export function fetchAddWorkMonth(data?: Api.WorkTicketManagementManage.WorkMonthAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/work_months',
    method: 'post',
    data
  });
}

export function fetchUpdateWorkMonth(data?: Api.WorkTicketManagementManage.WorkMonthUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/work_months/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteWorkMonth(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/work_months/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteWorkMonth(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/work_months',
    method: 'delete',
    data
  });
}

export function fetchExportWorkMonth(
  data?: Api.WorkTicketManagementManage.WorkMonthSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/work_months/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchWorkMonthImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/work_months/import-template' });
}

export function fetchPreviewImportWorkMonth(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/work_months/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorkMonth(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/work_months/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- MonthlyImportBatch ----
export function fetchGetMonthlyImportBatchList(data?: Api.WorkTicketManagementManage.MonthlyImportBatchSearchParams) {
  return request<Api.WorkTicketManagementManage.MonthlyImportBatchList>({
    url: '/business/work_ticket_management/monthly_import_batches/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetMonthlyImportBatch(id: string) {
  return request<Api.WorkTicketManagementManage.MonthlyImportBatch>({
    url: `/business/work_ticket_management/monthly_import_batches/${id}`,
    method: 'get'
  });
}

export function fetchAddMonthlyImportBatch(data?: Api.WorkTicketManagementManage.MonthlyImportBatchAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/monthly_import_batches',
    method: 'post',
    data
  });
}

export function fetchUpdateMonthlyImportBatch(data?: Api.WorkTicketManagementManage.MonthlyImportBatchUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/monthly_import_batches/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteMonthlyImportBatch(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/monthly_import_batches/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteMonthlyImportBatch(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/monthly_import_batches',
    method: 'delete',
    data
  });
}

export function fetchExportMonthlyImportBatch(
  data?: Api.WorkTicketManagementManage.MonthlyImportBatchSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/monthly_import_batches/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchMonthlyImportBatchImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/monthly_import_batches/import-template' });
}

export function fetchPreviewImportMonthlyImportBatch(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/monthly_import_batches/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportMonthlyImportBatch(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/monthly_import_batches/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- MonthlyImportRow ----
export function fetchGetMonthlyImportRowList(data?: Api.WorkTicketManagementManage.MonthlyImportRowSearchParams) {
  return request<Api.WorkTicketManagementManage.MonthlyImportRowList>({
    url: '/business/work_ticket_management/monthly_import_rows/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetMonthlyImportRow(id: string) {
  return request<Api.WorkTicketManagementManage.MonthlyImportRow>({
    url: `/business/work_ticket_management/monthly_import_rows/${id}`,
    method: 'get'
  });
}

export function fetchAddMonthlyImportRow(data?: Api.WorkTicketManagementManage.MonthlyImportRowAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/monthly_import_rows',
    method: 'post',
    data
  });
}

export function fetchUpdateMonthlyImportRow(data?: Api.WorkTicketManagementManage.MonthlyImportRowUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/monthly_import_rows/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteMonthlyImportRow(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/monthly_import_rows/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteMonthlyImportRow(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/monthly_import_rows',
    method: 'delete',
    data
  });
}

export function fetchExportMonthlyImportRow(
  data?: Api.WorkTicketManagementManage.MonthlyImportRowSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/monthly_import_rows/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchMonthlyImportRowImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/monthly_import_rows/import-template' });
}

export function fetchPreviewImportMonthlyImportRow(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/monthly_import_rows/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportMonthlyImportRow(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/monthly_import_rows/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- WorkTicket ----
export function fetchGetWorkTicketList(data?: Api.WorkTicketManagementManage.WorkTicketSearchParams) {
  return request<Api.WorkTicketManagementManage.WorkTicketList>({
    url: '/business/work_ticket_management/work_tickets/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetWorkTicket(id: string) {
  return request<Api.WorkTicketManagementManage.WorkTicket>({
    url: `/business/work_ticket_management/work_tickets/${id}`,
    method: 'get'
  });
}

export function fetchAddWorkTicket(data?: Api.WorkTicketManagementManage.WorkTicketAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/work_tickets',
    method: 'post',
    data
  });
}

export function fetchUpdateWorkTicket(data?: Api.WorkTicketManagementManage.WorkTicketUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/work_tickets/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteWorkTicket(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/work_tickets/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteWorkTicket(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/work_tickets',
    method: 'delete',
    data
  });
}

export function fetchExportWorkTicket(
  data?: Api.WorkTicketManagementManage.WorkTicketSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/work_tickets/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchWorkTicketImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/work_tickets/import-template' });
}

export function fetchPreviewImportWorkTicket(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/work_tickets/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorkTicket(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/work_tickets/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- WorkTicketAssignment ----
export function fetchGetWorkTicketAssignmentList(
  data?: Api.WorkTicketManagementManage.WorkTicketAssignmentSearchParams
) {
  return request<Api.WorkTicketManagementManage.WorkTicketAssignmentList>({
    url: '/business/work_ticket_management/work_ticket_assignments/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetWorkTicketAssignment(id: string) {
  return request<Api.WorkTicketManagementManage.WorkTicketAssignment>({
    url: `/business/work_ticket_management/work_ticket_assignments/${id}`,
    method: 'get'
  });
}

export function fetchAddWorkTicketAssignment(data?: Api.WorkTicketManagementManage.WorkTicketAssignmentAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/work_ticket_assignments',
    method: 'post',
    data
  });
}

export function fetchUpdateWorkTicketAssignment(
  data?: Api.WorkTicketManagementManage.WorkTicketAssignmentUpdateParams
) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/work_ticket_assignments/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteWorkTicketAssignment(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/work_ticket_assignments/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteWorkTicketAssignment(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/work_ticket_assignments',
    method: 'delete',
    data
  });
}

export function fetchExportWorkTicketAssignment(
  data?: Api.WorkTicketManagementManage.WorkTicketAssignmentSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/work_ticket_assignments/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchWorkTicketAssignmentImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/work_ticket_assignments/import-template' });
}

export function fetchPreviewImportWorkTicketAssignment(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/work_ticket_assignments/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorkTicketAssignment(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/work_ticket_assignments/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- WorkTimeEntry ----
export function fetchGetWorkTimeEntryList(data?: Api.WorkTicketManagementManage.WorkTimeEntrySearchParams) {
  return request<Api.WorkTicketManagementManage.WorkTimeEntryList>({
    url: '/business/work_ticket_management/work_time_entries/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetWorkTimeEntry(id: string) {
  return request<Api.WorkTicketManagementManage.WorkTimeEntry>({
    url: `/business/work_ticket_management/work_time_entries/${id}`,
    method: 'get'
  });
}

export function fetchAddWorkTimeEntry(data?: Api.WorkTicketManagementManage.WorkTimeEntryAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/work_time_entries',
    method: 'post',
    data
  });
}

export function fetchUpdateWorkTimeEntry(data?: Api.WorkTicketManagementManage.WorkTimeEntryUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/work_time_entries/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteWorkTimeEntry(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/work_time_entries/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteWorkTimeEntry(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/work_time_entries',
    method: 'delete',
    data
  });
}

export function fetchExportWorkTimeEntry(
  data?: Api.WorkTicketManagementManage.WorkTimeEntrySearchParams & { ids?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/work_time_entries/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchWorkTimeEntryImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/work_time_entries/import-template' });
}

export function fetchPreviewImportWorkTimeEntry(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/work_time_entries/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorkTimeEntry(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/work_time_entries/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- WorkMonthStatusLog ----
export function fetchGetWorkMonthStatusLogList(data?: Api.WorkTicketManagementManage.WorkMonthStatusLogSearchParams) {
  return request<Api.WorkTicketManagementManage.WorkMonthStatusLogList>({
    url: '/business/work_ticket_management/work_month_status_logs/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetWorkMonthStatusLog(id: string) {
  return request<Api.WorkTicketManagementManage.WorkMonthStatusLog>({
    url: `/business/work_ticket_management/work_month_status_logs/${id}`,
    method: 'get'
  });
}

export function fetchAddWorkMonthStatusLog(data?: Api.WorkTicketManagementManage.WorkMonthStatusLogAddParams) {
  return request<null, 'json'>({
    url: '/business/work_ticket_management/work_month_status_logs',
    method: 'post',
    data
  });
}

export function fetchUpdateWorkMonthStatusLog(data?: Api.WorkTicketManagementManage.WorkMonthStatusLogUpdateParams) {
  return request<null, 'json'>({
    url: `/business/work_ticket_management/work_month_status_logs/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteWorkMonthStatusLog(data?: Api.WorkTicketManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/work_ticket_management/work_month_status_logs/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteWorkMonthStatusLog(data?: Api.WorkTicketManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/work_ticket_management/work_month_status_logs',
    method: 'delete',
    data
  });
}

export function fetchExportWorkMonthStatusLog(
  data?: Api.WorkTicketManagementManage.WorkMonthStatusLogSearchParams & { ids?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/work_ticket_management/work_month_status_logs/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchWorkMonthStatusLogImportTemplate() {
  return request<ExcelDownload>({ url: '/business/work_ticket_management/work_month_status_logs/import-template' });
}

export function fetchPreviewImportWorkMonthStatusLog(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/work_ticket_management/work_month_status_logs/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorkMonthStatusLog(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/work_ticket_management/work_month_status_logs/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}
