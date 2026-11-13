"""
业务开发者的统一导入入口。

本模块重新导出常用类和函数，业务代码可从单一稳定位置导入，
无需深入引用 app.core.* 或 app.system.* 等内部模块：

    from app.utils import CRUDBase, CRUDRouter, Success, radar_log
"""

# ---- ORM 基类 & 枚举 ----
from app.core.base_model import AuditMixin as AuditMixin
from app.core.base_model import BaseModel as BaseModel
from app.core.base_model import IntEnum as IntEnum
from app.core.base_model import StatusType as StatusType
from app.core.base_model import StrEnum as StrEnum
from app.core.base_model import TreeMixin as TreeMixin

# ---- Schema 基类 ----
from app.core.base_schema import CommonIds as CommonIds
from app.core.base_schema import Custom as Custom
from app.core.base_schema import Fail as Fail
from app.core.base_schema import OfflineByRoleRequest as OfflineByRoleRequest
from app.core.base_schema import PageQueryBase as PageQueryBase
from app.core.base_schema import PageResponseModel as PageResponseModel
from app.core.base_schema import ResponseModel as ResponseModel
from app.core.base_schema import SchemaBase as SchemaBase
from app.core.base_schema import Success as Success
from app.core.base_schema import SuccessExtra as SuccessExtra
from app.core.base_schema import make_optional as make_optional
from app.core.business import BusinessModule as BusinessModule
from app.core.business import BusinessRouter as BusinessRouter
from app.core.business import DataPolicy as DataPolicy
from app.core.business import EventSpec as EventSpec
from app.core.business import PeriodicTask as PeriodicTask
from app.core.business import PermissionSpec as PermissionSpec
from app.core.business import PolicyContext as PolicyContext

# ---- 业务错误码 ----
from app.core.code import Code as Code

# ---- 配置 ----
from app.core.config import APP_SETTINGS as APP_SETTINGS

# ---- 常量 ----
from app.core.constants import SUPER_ADMIN_ROLE as SUPER_ADMIN_ROLE

# ---- CRUD 操作 ----
from app.core.crud import CRUDBase as CRUDBase
from app.core.crud import get_db_conn as get_db_conn

# ---- 上下文 & 鉴权 ----
from app.core.ctx import CTX_USER_ID as CTX_USER_ID
from app.core.ctx import get_current_user as get_current_user
from app.core.ctx import get_current_user_id as get_current_user_id
from app.core.ctx import has_button_code as has_button_code
from app.core.ctx import has_role_code as has_role_code
from app.core.ctx import is_super_admin as is_super_admin

# ---- 数据权限 ----
from app.core.data_scope import DataScopeType as DataScopeType
from app.core.data_scope import build_scope_filter as build_scope_filter
from app.core.dependency import DependAuth as DependAuth
from app.core.dependency import DependPermission as DependPermission
from app.core.dependency import require_buttons as require_buttons
from app.core.dependency import require_roles as require_roles

# ---- 事件总线 ----
from app.core.events import emit as emit
from app.core.events import on as on
from app.core.excel import ExcelColumn as ExcelColumn
from app.core.excel import ExcelConfig as ExcelConfig
from app.core.excel import ExcelDetail as ExcelDetail
from app.core.excel import ExcelImportOptions as ExcelImportOptions
from app.core.excel import ExcelImportResult as ExcelImportResult
from app.core.excel import ExcelPreview as ExcelPreview
from app.core.excel import parse_excel as parse_excel
from app.core.excel import write_excel as write_excel
from app.core.excel import write_excel_sheets as write_excel_sheets
from app.core.exceptions import BizError as BizError
from app.core.exceptions import SchemaValidationError as SchemaValidationError

# ---- 日志 & 监控 ----
from app.core.log import log as log
from app.core.outbox import dispatch_outbox_once as dispatch_outbox_once
from app.core.outbox import enqueue_outbox_event as enqueue_outbox_event
from app.core.outbox import make_outbox_dispatch_task as make_outbox_dispatch_task
from app.core.policy import apply_data_policy as apply_data_policy
from app.core.policy import assert_object_policy as assert_object_policy
from app.core.policy import build_policy_context as build_policy_context
from app.core.policy import check_object_policy as check_object_policy
from app.core.router import CRUDRouter as CRUDRouter
from app.core.router import SearchFieldConfig as SearchFieldConfig
from app.core.soft_delete import SoftDeleteMixin as SoftDeleteMixin

# ---- Sqids 编解码 ----
from app.core.sqids import decode_id as decode_id
from app.core.sqids import encode_id as encode_id

# ---- 状态机 ----
from app.core.state_machine import StateMachine as StateMachine

# ---- 数据工具 ----
from app.core.tools import camel_case_convert as camel_case_convert
from app.core.tools import orjson_dumps as orjson_dumps
from app.core.tools import snake_case_convert as snake_case_convert
from app.core.tools import time_to_timestamp as time_to_timestamp
from app.core.tools import timestamp_to_time as timestamp_to_time
from app.core.tools import to_camel_case as to_camel_case
from app.core.tools import to_lower_camel_case as to_lower_camel_case
from app.core.tools import to_snake_case as to_snake_case
from app.core.tools import to_upper_camel_case as to_upper_camel_case

# ---- 约束类型别名 ----
from app.core.types import Int16 as Int16
from app.core.types import Int32 as Int32
from app.core.types import Int64 as Int64
from app.core.types import SqidId as SqidId
from app.core.types import SqidPath as SqidPath
from app.system.radar.developer import radar_log as radar_log

# ---- 安全 ----
from app.system.security import create_access_token as create_access_token
from app.system.security import get_password_hash as get_password_hash
from app.system.security import verify_password as verify_password
