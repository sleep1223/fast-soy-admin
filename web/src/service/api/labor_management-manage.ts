import { request } from '../request';
import { createExcelFormData } from '@/utils/excel';
import type { ExcelDownload, ExcelImportOptions, ExcelImportResult, ExcelPreview } from '@/utils/excel';

// ---- LaborProject ----
export function fetchGetLaborProjectList(data?: Api.LaborManagementManage.LaborProjectSearchParams) {
  return request<Api.LaborManagementManage.LaborProjectList>({
    url: '/business/labor_management/labor_projects/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetLaborProject(id: string) {
  return request<Api.LaborManagementManage.LaborProject>({
    url: `/business/labor_management/labor_projects/${id}`,
    method: 'get'
  });
}

export function fetchAddLaborProject(data?: Api.LaborManagementManage.LaborProjectAddParams) {
  return request<null, 'json'>({
    url: '/business/labor_management/labor_projects',
    method: 'post',
    data
  });
}

export function fetchUpdateLaborProject(data?: Api.LaborManagementManage.LaborProjectUpdateParams) {
  return request<null, 'json'>({
    url: `/business/labor_management/labor_projects/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteLaborProject(data?: Api.LaborManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/labor_management/labor_projects/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteLaborProject(data?: Api.LaborManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/labor_management/labor_projects',
    method: 'delete',
    data
  });
}

export function fetchExportLaborProject(
  data?: Api.LaborManagementManage.LaborProjectSearchParams & { ids?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/labor_management/labor_projects/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchLaborProjectImportTemplate() {
  return request<ExcelDownload>({ url: '/business/labor_management/labor_projects/import-template' });
}

export function fetchPreviewImportLaborProject(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/labor_management/labor_projects/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportLaborProject(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/labor_management/labor_projects/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- LaborWorker ----
export function fetchGetLaborWorkerList(data?: Api.LaborManagementManage.LaborWorkerSearchParams) {
  return request<Api.LaborManagementManage.LaborWorkerList>({
    url: '/business/labor_management/labor_workers/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetLaborWorker(id: string) {
  return request<Api.LaborManagementManage.LaborWorker>({
    url: `/business/labor_management/labor_workers/${id}`,
    method: 'get'
  });
}

export function fetchAddLaborWorker(data?: Api.LaborManagementManage.LaborWorkerAddParams) {
  return request<null, 'json'>({
    url: '/business/labor_management/labor_workers',
    method: 'post',
    data
  });
}

export function fetchUpdateLaborWorker(data?: Api.LaborManagementManage.LaborWorkerUpdateParams) {
  return request<null, 'json'>({
    url: `/business/labor_management/labor_workers/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteLaborWorker(data?: Api.LaborManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/labor_management/labor_workers/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteLaborWorker(data?: Api.LaborManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/labor_management/labor_workers',
    method: 'delete',
    data
  });
}

export function fetchExportLaborWorker(
  data?: Api.LaborManagementManage.LaborWorkerSearchParams & { ids?: string[]; parentFields?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/labor_management/labor_workers/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchLaborWorkerImportTemplate() {
  return request<ExcelDownload>({ url: '/business/labor_management/labor_workers/import-template' });
}

export function fetchPreviewImportLaborWorker(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/labor_management/labor_workers/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportLaborWorker(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/labor_management/labor_workers/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

// ---- LaborWorkHour ----
export function fetchGetLaborWorkHourList(data?: Api.LaborManagementManage.LaborWorkHourSearchParams) {
  return request<Api.LaborManagementManage.LaborWorkHourList>({
    url: '/business/labor_management/labor_work_hours/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetLaborWorkHour(id: string) {
  return request<Api.LaborManagementManage.LaborWorkHour>({
    url: `/business/labor_management/labor_work_hours/${id}`,
    method: 'get'
  });
}

export function fetchAddLaborWorkHour(data?: Api.LaborManagementManage.LaborWorkHourAddParams) {
  return request<null, 'json'>({
    url: '/business/labor_management/labor_work_hours',
    method: 'post',
    data
  });
}

export function fetchUpdateLaborWorkHour(data?: Api.LaborManagementManage.LaborWorkHourUpdateParams) {
  return request<null, 'json'>({
    url: `/business/labor_management/labor_work_hours/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteLaborWorkHour(data?: Api.LaborManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/labor_management/labor_work_hours/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteLaborWorkHour(data?: Api.LaborManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/labor_management/labor_work_hours',
    method: 'delete',
    data
  });
}

export function fetchExportLaborWorkHour(
  data?: Api.LaborManagementManage.LaborWorkHourSearchParams & { ids?: string[] }
) {
  return request<ExcelDownload>({
    url: '/business/labor_management/labor_work_hours/export',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchLaborWorkHourImportTemplate() {
  return request<ExcelDownload>({ url: '/business/labor_management/labor_work_hours/import-template' });
}

export function fetchPreviewImportLaborWorkHour(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/labor_management/labor_work_hours/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportLaborWorkHour(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelImportResult>({
    url: '/business/labor_management/labor_work_hours/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}
