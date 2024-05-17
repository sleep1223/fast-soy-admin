from datetime import datetime
from enum import Enum
from uuid import UUID

from tortoise import models, fields

from app.settings import APP_SETTINGS
from app.utils.tools import to_lower_camel_case


class BaseModel(models.Model):
    async def to_dict(
            self, include_fields: list[str] | None = None, exclude_fields: list[str] | None = None, m2m: bool = False
    ):
        include_fields = include_fields or []
        exclude_fields = exclude_fields or []

        d = {}
        for field in self._meta.db_fields:
            if (not include_fields or field in include_fields) and (not exclude_fields or field not in exclude_fields):
                value = getattr(self, field)
                if isinstance(value, datetime):
                    value = value.strftime(APP_SETTINGS.DATETIME_FORMAT)
                elif isinstance(value, UUID):
                    value = str(value)
                d[to_lower_camel_case(field)] = value

        if m2m:
            for field in self._meta.m2m_fields:
                if (not include_fields or field in include_fields) and (
                        not exclude_fields or field not in exclude_fields
                ):
                    values = [value for value in await getattr(self, field).all().values()]
                    for value in values:
                        _value = value.copy()
                        for k, v in _value.items():
                            if isinstance(v, datetime):
                                v = v.strftime(APP_SETTINGS.DATETIME_FORMAT)
                            elif isinstance(v, UUID):
                                v = str(v)
                            value.pop(k)
                            value[to_lower_camel_case(k)] = v
                    d[to_lower_camel_case(field)] = values
        return d

    class Meta:
        abstract = True


class TimestampMixin:
    create_time = fields.DatetimeField(auto_now_add=True)
    update_time = fields.DatetimeField(auto_now=True)


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class IntEnum(int, EnumBase):
    ...


class StrEnum(str, EnumBase):
    ...


class MethodType(str, Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"


class LogType(str, Enum):
    ApiLog = "1"
    UserLog = "2"
    AdminLog = "3"
    SystemLog = "4"


class LogDetailType(str, Enum):
    """
    1000-1999 内置
    1100-1199 系统
    1200-1299 用户
    1300-1399 API
    1400-1499 菜单
    1500-1599 角色
    1600-1699 用户
    """
    SystemStart = "1101"
    SystemStop = "1102"

    UserLoginSuccess = "1201"
    UserAuthRefreshTokenSuccess = "1202"
    UserLoginGetUserInfo = "1203"
    UserLoginUserNameVaild = "1211"
    UserLoginErrorPassword = "1212"
    UserLoginForbid = "1213"

    ApiGetList = "1301"
    ApiGetTree = "1302"
    ApiRefresh = "1303"

    ApiGetOne = "1311"
    ApiCreateOne = "1312"
    ApiUpdateOne = "1313"
    ApiDeleteOne = "1314"
    ApiBatchDelete = "1315"

    MenuGetList = "1401"
    MenuGetTree = "1402"
    MenuGetPages = "1403"
    MenuGetButtonsTree = "1404"

    MenuGetOne = "1411"
    MenuCreateOne = "1412"
    MenuUpdateOne = "1413"
    MenuDeleteOne = "1414"
    MenuBatchDeleteOne = "1415"

    RoleGetList = "1501"
    RoleGetMenus = "1502"
    RoleUpdateMenus = "1503"
    RoleGetButtons = "1504"
    RoleUpdateButtons = "1505"
    RoleGetApis = "1506"
    RoleUpdateApis = "1507"

    RoleGetOne = "1511"
    RoleCreateOne = "1512"
    RoleUpdateOne = "1513"
    RoleDeleteOne = "1514"
    RoleBatchDeleteOne = "1515"

    UserGetList = "1601"
    UserGetOne = "1611"
    UserCreateOne = "1612"
    UserUpdateOne = "1613"
    UserDeleteOne = "1614"
    UserBatchDeleteOne = "1615"


class StatusType(str, Enum):
    enable = "1"
    disable = "2"


class GenderType(str, Enum):
    male = "1"
    female = "2"
    unknow = "3"  # Soybean上没有


class MenuType(str, Enum):
    catalog = "1"  # 目录
    menu = "2"  # 菜单


class IconType(str, Enum):
    iconify = "1"
    local = "2"


__all__ = ["BaseModel", "TimestampMixin", "EnumBase", "IntEnum", "StrEnum", "MethodType", "LogType", "LogDetailType", "StatusType", "GenderType", "MenuType", "IconType"]
