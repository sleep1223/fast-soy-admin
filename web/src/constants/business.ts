import { transformRecordToOption } from '@/utils/common';

export const enableStatusRecord: Record<Api.Common.EnableStatus, App.I18n.I18nKey> = {
  '1': 'page.manage.common.status.enable',
  '2': 'page.manage.common.status.disable'
};

export const enableStatusOptions = transformRecordToOption(enableStatusRecord);

export const logDetailTypeRecord: Record<Api.SystemManage.logDetailTypes, App.I18n.I18nKey> = {
  '1101': 'page.manage.log.logDetailTypes.SystemStart',
  '1102': 'page.manage.log.logDetailTypes.SystemStop',
  '1201': 'page.manage.log.logDetailTypes.UserLoginSuccess',
  '1202': 'page.manage.log.logDetailTypes.UserAuthRefreshTokenSuccess',
  '1203': 'page.manage.log.logDetailTypes.UserLoginGetUserInfo',
  '1211': 'page.manage.log.logDetailTypes.UserLoginUserNameVaild',
  '1212': 'page.manage.log.logDetailTypes.UserLoginErrorPassword',
  '1213': 'page.manage.log.logDetailTypes.UserLoginForbid',
  '1301': 'page.manage.log.logDetailTypes.ApiGetList',
  '1302': 'page.manage.log.logDetailTypes.ApiGetTree',
  '1303': 'page.manage.log.logDetailTypes.ApiRefresh',
  '1311': 'page.manage.log.logDetailTypes.ApiGetOne',
  '1312': 'page.manage.log.logDetailTypes.ApiCreateOne',
  '1313': 'page.manage.log.logDetailTypes.ApiUpdateOne',
  '1314': 'page.manage.log.logDetailTypes.ApiDeleteOne',
  '1315': 'page.manage.log.logDetailTypes.ApiBatchDelete',
  '1401': 'page.manage.log.logDetailTypes.MenuGetList',
  '1402': 'page.manage.log.logDetailTypes.MenuGetTree',
  '1403': 'page.manage.log.logDetailTypes.MenuGetPages',
  '1404': 'page.manage.log.logDetailTypes.MenuGetButtonsTree',
  '1411': 'page.manage.log.logDetailTypes.MenuGetOne',
  '1412': 'page.manage.log.logDetailTypes.MenuCreateOne',
  '1413': 'page.manage.log.logDetailTypes.MenuUpdateOne',
  '1414': 'page.manage.log.logDetailTypes.MenuDeleteOne',
  '1415': 'page.manage.log.logDetailTypes.MenuBatchDeleteOne',
  '1501': 'page.manage.log.logDetailTypes.RoleGetList',
  '1502': 'page.manage.log.logDetailTypes.RoleGetMenus',
  '1503': 'page.manage.log.logDetailTypes.RoleUpdateMenus',
  '1504': 'page.manage.log.logDetailTypes.RoleGetButtons',
  '1505': 'page.manage.log.logDetailTypes.RoleUpdateButtons',
  '1506': 'page.manage.log.logDetailTypes.RoleGetApis',
  '1507': 'page.manage.log.logDetailTypes.RoleUpdateApis',
  '1511': 'page.manage.log.logDetailTypes.RoleGetOne',
  '1512': 'page.manage.log.logDetailTypes.RoleCreateOne',
  '1513': 'page.manage.log.logDetailTypes.RoleUpdateOne',
  '1514': 'page.manage.log.logDetailTypes.RoleDeleteOne',
  '1515': 'page.manage.log.logDetailTypes.RoleBatchDeleteOne',
  '1601': 'page.manage.log.logDetailTypes.UserGetList',
  '1611': 'page.manage.log.logDetailTypes.UserGetOne',
  '1612': 'page.manage.log.logDetailTypes.UserCreateOne',
  '1613': 'page.manage.log.logDetailTypes.UserUpdateOne',
  '1614': 'page.manage.log.logDetailTypes.UserDeleteOne',
  '1615': 'page.manage.log.logDetailTypes.UserBatchDeleteOne'
};

export const logDetailTypeOptions = transformRecordToOption(logDetailTypeRecord);

export const logTypeRecord: Record<Api.SystemManage.logTypes, App.I18n.I18nKey> = {
  '1': 'page.manage.log.logTypes.ApiLog',
  '2': 'page.manage.log.logTypes.UserLog',
  '3': 'page.manage.log.logTypes.AdminLog',
  '4': 'page.manage.log.logTypes.SystemLog'
};

export const logTypeOptions = transformRecordToOption(logTypeRecord);

export const apiMethodRecord: Record<Api.SystemManage.methods, App.I18n.I18nKey> = {
  get: 'page.manage.api.methods.GET',
  post: 'page.manage.api.methods.POST',
  put: 'page.manage.api.methods.PUT',
  patch: 'page.manage.api.methods.PATCH',
  delete: 'page.manage.api.methods.DELETE'
};

export const apiMethodOptions = transformRecordToOption(apiMethodRecord);

export const userGenderRecord: Record<Api.SystemManage.UserGender, App.I18n.I18nKey> = {
  '1': 'page.manage.user.gender.male',
  '2': 'page.manage.user.gender.female',
  '3': 'page.manage.user.gender.unknow'
};

export const userGenderOptions = transformRecordToOption(userGenderRecord);

export const menuTypeRecord: Record<Api.SystemManage.MenuType, App.I18n.I18nKey> = {
  '1': 'page.manage.menu.type.directory',
  '2': 'page.manage.menu.type.menu'
};

export const menuTypeOptions = transformRecordToOption(menuTypeRecord);

export const menuIconTypeRecord: Record<Api.SystemManage.IconType, App.I18n.I18nKey> = {
  '1': 'page.manage.menu.iconType.iconify',
  '2': 'page.manage.menu.iconType.local'
};

export const menuIconTypeOptions = transformRecordToOption(menuIconTypeRecord);
