import type { CustomAxiosRequestConfig } from '@sa/axios';
import { request } from '../request';

/** Remove null, undefined, and empty string values from params to avoid FastAPI 422 errors */
function cleanParams<T extends Record<string, any>>(params?: T): Partial<T> | undefined {
  if (!params) return undefined;
  const cleaned: Record<string, any> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      cleaned[key] = value;
    }
  }
  return Object.keys(cleaned).length > 0 ? (cleaned as Partial<T>) : undefined;
}

/** Radar is outside /api/v1 but must reuse the authenticated client and its refresh/retry flow. */
function radarRequest<T>(config: CustomAxiosRequestConfig) {
  return request<T>({ baseURL: '/__radar/api', ...config });
}

/** get radar stats overview */
export function fetchRadarStats(hours?: number) {
  return radarRequest<Api.Radar.Stats>({
    url: '/stats',
    method: 'get',
    params: cleanParams({ hours })
  });
}

/** get radar dashboard stats */
export function fetchRadarDashboard(hours?: number) {
  return radarRequest<Api.Radar.DashboardStats>({
    url: '/dashboard',
    method: 'get',
    params: { hours: hours || 1 }
  });
}

/** get radar request list */
export function fetchRadarRequests(params?: Api.Radar.RequestSearchParams) {
  return radarRequest<Api.Radar.RequestList>({
    url: '/requests',
    method: 'get',
    params: cleanParams(params)
  });
}

/** get radar request detail */
export function fetchRadarRequestDetail(xRequestId: string) {
  return radarRequest<Api.Radar.RequestDetail>({
    url: `/requests/${xRequestId}`,
    method: 'get'
  });
}

/** get radar SQL query list */
export function fetchRadarQueries(params?: Api.Radar.QuerySearchParams) {
  return radarRequest<Api.Radar.QueryList>({
    url: '/queries',
    method: 'get',
    params: cleanParams(params)
  });
}

/** get radar exception list */
export function fetchRadarExceptions(params?: Api.Radar.ExceptionSearchParams) {
  return radarRequest<Api.Radar.ExceptionList>({
    url: '/exceptions',
    method: 'get',
    params: cleanParams(params)
  });
}

/** toggle exception resolved status */
export function fetchRadarExceptionResolve(xRequestId: string, resolved: boolean) {
  return radarRequest<null>({
    url: `/exceptions/${xRequestId}/resolve`,
    method: 'put',
    data: { resolved }
  });
}

/** purge old radar data */
export function fetchRadarPurge(retentionHours?: number) {
  return radarRequest<{ deleted_count: number }>({
    url: '/purge',
    method: 'delete',
    params: { retention_hours: retentionHours }
  });
}

/** get system monitor overview */
export function fetchMonitorOverview() {
  return radarRequest<Api.Monitor.Overview>({
    url: '/monitor/overview',
    method: 'get'
  });
}

/** get system monitor realtime data */
export function fetchMonitorRealtime() {
  return radarRequest<Api.Monitor.Realtime>({
    url: '/monitor/realtime',
    method: 'get'
  });
}
