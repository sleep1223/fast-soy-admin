import { createExcelFormData } from '@/utils/excel';
import type { ExcelImportOptions, ExcelImportResult, ExcelPreview } from '@/utils/excel';
import { request } from '../request';

const base = '/business/work_ticket_management';

export interface AssetProject {
  id: string;
  partNo: string;
  orderCount: number;
}

export interface AssetOrder {
  id: string;
  orderNo: string;
  name: string;
  ticketCount: number;
}

interface AssetPage<T> {
  records: T[];
  total: number;
  current: number;
  size: number;
}

export interface AssetAllocation {
  id: string;
  workerId: string;
  workerName: string;
  assignedOn: string;
  hours: string | null;
}

export interface AssetTicket {
  id: string;
  ticketCode: string;
  codeSource: 'manual' | 'ocr';
  totalHours: string | null;
  assignedHours: string;
  allocations: AssetAllocation[];
}

export interface TicketInput {
  ticketCode: string;
  codeSource: AssetTicket['codeSource'];
  totalHours: number | null;
}

interface AllocationInput {
  workerId: string;
  assignedOn: string;
  hours: number | null;
}

interface AssetReportRow {
  workerId: string;
  workerName: string;
  productionUnitName: string | null;
  allocationCount: number;
  hours: string;
}

interface ProjectImportResult extends ExcelImportResult {
  matchedOrderCount: number;
  unmatchedProjectCount: number;
}

export function fetchGetWorkProjectList(data: { current: number; size: number; partNo: string }) {
  return request<AssetPage<AssetProject>, 'json'>({ url: `${base}/work_projects/search`, method: 'post', data });
}

export function fetchPreviewImportWorkProject(file: File, options?: ExcelImportOptions) {
  return request<ExcelPreview>({
    url: `${base}/work_projects/import-preview`,
    method: 'post',
    data: createExcelFormData(file, options),
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportWorkProject(file: File, options?: ExcelImportOptions) {
  return request<ProjectImportResult>({
    url: `${base}/work_projects/import`,
    method: 'post',
    data: createExcelFormData(file, options),
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchGetWorkProjectOrderList(projectId: string, data: { current: number; size: number }) {
  return request<AssetPage<AssetOrder>, 'json'>({
    url: `${base}/work_projects/${projectId}/orders/search`,
    method: 'post',
    data
  });
}

export function fetchWorkAssetTickets(orderId: string) {
  return request<AssetTicket[]>({ url: `${base}/work_project_orders/${orderId}/tickets` });
}

export function fetchAddWorkAssetTicket(orderId: string, data: TicketInput) {
  return request<string, 'json'>({ url: `${base}/work_project_orders/${orderId}/tickets`, method: 'post', data });
}

export function fetchUpdateWorkAssetTicket(ticketId: string, data: TicketInput) {
  return request<null, 'json'>({ url: `${base}/work_asset_tickets/${ticketId}`, method: 'put', data });
}

export function fetchAddWorkAssetAllocation(ticketId: string, data: AllocationInput) {
  return request<string, 'json'>({ url: `${base}/work_asset_tickets/${ticketId}/allocations`, method: 'post', data });
}

export function fetchUpdateWorkAssetAllocation(ticketId: string, allocationId: string, data: AllocationInput) {
  return request<null, 'json'>({
    url: `${base}/work_asset_tickets/${ticketId}/allocations/${allocationId}`,
    method: 'put',
    data
  });
}

export function fetchWorkAssetReport(data: { startDate: string; endDate: string; productionUnitId: string | null }) {
  return request<AssetReportRow[], 'json'>({ url: `${base}/work_asset_allocations/report`, method: 'post', data });
}
