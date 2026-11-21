import { request } from '../request';
import { createExcelFormData } from '@/utils/excel';
import type { ExcelDownload, ExcelImportOptions, ExcelPreview } from '@/utils/excel';

// ---- Order ----
export function fetchGetOrderList(data?: Api.OrderManagementManage.OrderSearchParams) {
  return request<Api.OrderManagementManage.OrderList>({
    url: '/business/order_management/orders/search',
    method: 'post',
    data: data ?? {}
  });
}

export function fetchGetOrder(id: string) {
  return request<Api.OrderManagementManage.Order>({
    url: `/business/order_management/orders/${id}`,
    method: 'get'
  });
}

export function fetchAddOrder(data?: Api.OrderManagementManage.OrderAddParams) {
  return request<null, 'json'>({
    url: '/business/order_management/orders',
    method: 'post',
    data
  });
}

export function fetchUpdateOrder(data?: Api.OrderManagementManage.OrderUpdateParams) {
  return request<null, 'json'>({
    url: `/business/order_management/orders/${data?.id}`,
    method: 'patch',
    data
  });
}

export function fetchDeleteOrder(data?: Api.OrderManagementManage.CommonDeleteParams) {
  return request<null>({
    url: `/business/order_management/orders/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteOrder(data?: Api.OrderManagementManage.CommonBatchDeleteParams) {
  return request<null>({
    url: '/business/order_management/orders',
    method: 'delete',
    data
  });
}

export function fetchExportOrder(data?: Api.OrderManagementManage.OrderSearchParams & { ids?: string[] }) {
  return request<ExcelDownload>({ url: '/business/order_management/orders/export', method: 'post', data: data ?? {} });
}

export function fetchOrderImportTemplate() {
  return request<ExcelDownload>({ url: '/business/order_management/orders/import-template' });
}

export function fetchPreviewImportOrder(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<ExcelPreview>({
    url: '/business/order_management/orders/import-preview',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}

export function fetchImportOrder(file: File, options?: ExcelImportOptions) {
  const data = createExcelFormData(file, options);
  return request<{ importedCount: number }>({
    url: '/business/order_management/orders/import',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  });
}
