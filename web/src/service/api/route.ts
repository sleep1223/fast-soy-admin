import { request } from '../request';

/** 获取常量路由 */
export function fetchGetConstantRoutes() {
  return request<Api.Route.MenuRoute[]>({ url: '/route/constant-routes' });
}

/** 获取用户路由 */
export function fetchGetUserRoutes() {
  return request<Api.Route.UserRoute>({ url: '/route/user-routes' });
}

/**
 * 检查路由是否存在
 *
 * @param routeName 路由名称
 */
export function fetchIsRouteExist(routeName: string) {
  return request<boolean>({ url: `/route/${routeName}/exists` });
}
