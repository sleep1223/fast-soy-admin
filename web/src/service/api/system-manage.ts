import { request } from '../request';

/** get role list */
export function fetchGetRoleList(params?: Api.SystemManage.RoleSearchParams) {
  return request<Api.SystemManage.RoleList>({
    url: '/system-manage/roles',
    method: 'get',
    params
  });
}

/** get user list */
export function fetchGetUserList(params?: Api.SystemManage.UserSearchParams) {
  return request<Api.SystemManage.UserList>({
    url: '/system-manage/users',
    method: 'get',
    params
  });
}

/** get menu list */
export function fetchGetMenuList() {
  return request<Api.SystemManage.MenuList>({
    url: '/system-manage/menus',
    method: 'get'
  });
}

/** get all pages */
export function fetchGetAllPages() {
  return request<string[]>({
    url: '/system-manage/menus/pages/',
    method: 'get'
  });
}

/** get menu tree */
export function fetchGetMenuTree() {
  return request<Api.SystemManage.MenuTree[]>({
    url: '/system-manage/menus/tree/',
    method: 'get'
  });
}

/** get menu button tree */
export function fetchGetMenuButtonTree() {
  return request<Api.SystemManage.ButtonTree[]>({
    url: '/system-manage/menus/buttons/tree/',
    method: 'get'
  });
}

/** get log list */
export function fetchGetLogList(params?: Api.SystemManage.LogSearchParams) {
  return request<Api.SystemManage.LogList>({
    url: '/system-manage/logs',
    method: 'get',
    params
  });
}

/** delete log */
export function fetchDeleteLog(data?: Api.SystemManage.CommonDeleteParams) {
  return request<Api.SystemManage.LogList>({
    url: `/system-manage/logs/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteLog(data?: Api.SystemManage.CommonBatchDeleteParams) {
  return request<Api.SystemManage.LogList>({
    url: '/system-manage/logs',
    method: 'delete',
    params: { ids: data?.ids.join(',') }
  });
}
/** update log */
export function fetchUpdateLog(data?: Api.SystemManage.LogUpdateParams) {
  return request<Api.SystemManage.LogList, 'json'>({
    url: `/system-manage/logs/${data?.id}`,
    method: 'patch',
    data
  });
}

/** get api tree */
export function fetchGetApiTree() {
  return request<Api.SystemManage.MenuTree[]>({
    url: '/system-manage/apis/tree/',
    method: 'get'
  });
}

/** refresh api from fastapi */
export function fetchRefreshAPI() {
  return request<Api.SystemManage.ApiList>({
    url: '/system-manage/apis/refresh/',
    method: 'post'
  });
}

/** get api list */
export function fetchGetApiList(params?: Api.SystemManage.ApiSearchParams) {
  return request<Api.SystemManage.ApiList>({
    url: '/system-manage/apis',
    method: 'get',
    params
  });
}

/** add api */
export function fetchAddApi(data?: Api.SystemManage.ApiAddParams) {
  return request<Api.SystemManage.ApiList, 'json'>({
    url: '/system-manage/apis',
    method: 'post',
    data
  });
}

/** delete api */
export function fetchDeleteApi(data?: Api.SystemManage.CommonDeleteParams) {
  return request<Api.SystemManage.ApiList>({
    url: `/system-manage/apis/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteApi(data?: Api.SystemManage.CommonBatchDeleteParams) {
  return request<Api.SystemManage.ApiList>({
    url: '/system-manage/apis',
    method: 'delete',
    params: { ids: data?.ids.join(',') }
  });
}
/** update api */
export function fetchUpdateApi(data?: Api.SystemManage.ApiUpdateParams) {
  return request<Api.SystemManage.ApiList, 'json'>({
    url: `/system-manage/apis/${data?.id}`,
    method: 'patch',
    data
  });
}

/** add user */
export function fetchAddUser(data?: Api.SystemManage.UserAddParams) {
  return request<Api.SystemManage.UserList, 'json'>({
    url: '/system-manage/users',
    method: 'post',
    data
  });
}

/** delete user */
export function fetchDeleteUser(data?: Api.SystemManage.CommonDeleteParams) {
  return request<Api.SystemManage.UserList>({
    url: `/system-manage/users/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteUser(data?: Api.SystemManage.CommonBatchDeleteParams) {
  return request<Api.SystemManage.UserList>({
    url: '/system-manage/users',
    method: 'delete',
    params: { ids: data?.ids.join(',') }
  });
}
/** update user */
export function fetchUpdateUser(data?: Api.SystemManage.UserUpdateParams) {
  return request<Api.SystemManage.UserList, 'json'>({
    url: `/system-manage/users/${data?.id}`,
    method: 'patch',
    data
  });
}

/** add role */
export function fetchAddRole(data?: Api.SystemManage.RoleUpdateParams) {
  return request<Api.SystemManage.RoleList, 'json'>({
    url: '/system-manage/roles',
    method: 'post',
    data
  });
}

/** delete role */
export function fetchDeleteRole(data?: Api.SystemManage.CommonDeleteParams) {
  return request<Api.SystemManage.RoleList>({
    url: `/system-manage/roles/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteRole(data?: Api.SystemManage.CommonBatchDeleteParams) {
  return request<Api.SystemManage.RoleList>({
    url: '/system-manage/roles',
    method: 'delete',
    params: { ids: data?.ids.join(',') }
  });
}

/** update role */
export function fetchUpdateRole(data?: Api.SystemManage.RoleUpdateParams) {
  return request<Api.SystemManage.RoleList, 'json'>({
    url: `/system-manage/roles/${data?.id}`,
    method: 'patch',
    data
  });
}

/** get role menu ids */
export function fetchGetRoleMenu(data?: Api.SystemManage.RoleAuthorizedParams) {
  return request<Api.SystemManage.RoleAuthorizedList>({
    url: `/system-manage/roles/${data?.id}/menus`,
    method: 'get'
  });
}

/** update role menu ids */
export function fetchUpdateRoleMenu(data?: Api.SystemManage.RoleAuthorizedList) {
  return request<Api.SystemManage.RoleAuthorizedList>({
    url: `/system-manage/roles/${data?.id}/menus`,
    method: 'patch',
    data
  });
}

/** get role button ids */
export function fetchGetRoleButton(data?: Api.SystemManage.RoleAuthorizedParams) {
  return request<Api.SystemManage.RoleAuthorizedList>({
    url: `/system-manage/roles/${data?.id}/buttons`,
    method: 'get'
  });
}

/** update role button ids */
export function fetchUpdateRoleButton(data?: Api.SystemManage.RoleAuthorizedList) {
  return request<Api.SystemManage.RoleAuthorizedList>({
    url: `/system-manage/roles/${data?.id}/buttons`,
    method: 'patch',
    data
  });
}

/** get role api ids */
export function fetchGetRoleApi(data?: Api.SystemManage.RoleAuthorizedParams) {
  return request<Api.SystemManage.RoleAuthorizedList>({
    url: `/system-manage/roles/${data?.id}/apis`,
    method: 'get'
  });
}

/** update role api ids */
export function fetchUpdateRoleApi(data?: Api.SystemManage.RoleAuthorizedList) {
  return request<Api.SystemManage.RoleAuthorizedList>({
    url: `/system-manage/roles/${data?.id}/apis`,
    method: 'patch',
    data
  });
}

/** add menu */
export function fetchAddMenu(data?: Api.SystemManage.MenuAddParams) {
  return request<Api.SystemManage.MenuList, 'json'>({
    url: '/system-manage/menus',
    method: 'post',
    data
  });
}

/** delete menu */
export function fetchDeleteMenu(data?: Api.SystemManage.CommonDeleteParams) {
  return request<Api.SystemManage.MenuList>({
    url: `/system-manage/menus/${data?.id}`,
    method: 'delete'
  });
}

export function fetchBatchDeleteMenu(data?: Api.SystemManage.CommonBatchDeleteParams) {
  return request<Api.SystemManage.MenuList>({
    url: '/system-manage/menus',
    method: 'delete',
    params: { ids: data?.ids.join(',') }
  });
}

/** update menu */
export function fetchUpdateMenu(data?: Api.SystemManage.MenuUpdateParams) {
  return request<Api.SystemManage.MenuList, 'json'>({
    url: `/system-manage/menus/${data?.id}`,
    method: 'patch',
    data
  });
}
