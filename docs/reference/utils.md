# app.utils — 业务开发者的统一入口

`app/utils/__init__.py` 把业务模块经常用到的类与函数集中重新导出，避免在业务代码里到处出现 `from app.core.xxx import ...` / `from app.system.xxx import ...`。

::: tip 强约定
业务模块（`app/business/<x>/`）的 import 入口**统一走 `app.utils`**。`app/system/` 内部为避免循环依赖，仍直接从 `app/core/*` 引入。
:::

## 一行 import 速查

```python
from app.utils import (
    # ORM 基类与枚举
    BaseModel, AuditMixin, TreeMixin, SoftDeleteMixin,
    StatusType, IntEnum, StrEnum,

    # Schema 基类与响应封装
    SchemaBase, PageQueryBase,
    Success, Fail, SuccessExtra,
    CommonIds, OfflineByRoleRequest,
    ResponseModel, PageResponseModel,
    Custom, make_optional,

    # CRUD
    CRUDBase, get_db_conn,
    CRUDRouter, SearchFieldConfig,

    # 业务码 & 异常
    Code, BizError, SchemaValidationError,

    # 鉴权 & 上下文
    DependAuth, DependPermission,
    require_buttons, require_roles,
    CTX_USER_ID,
    get_current_user, get_current_user_id,
    is_super_admin, has_role_code, has_button_code,

    # 数据权限
    DataScopeType, build_scope_filter,

    # 事件 & 状态机
    emit, on,
    StateMachine,

    # Sqids & 字段约束
    encode_id, decode_id,
    SqidId, SqidPath,
    Int16, Int32, Int64,

    # 配置 & 常量 & 日志
    APP_SETTINGS, SUPER_ADMIN_ROLE, log,

    # 工具
    camel_case_convert, snake_case_convert,
    to_camel_case, to_snake_case,
    to_lower_camel_case, to_upper_camel_case,
    time_to_timestamp, timestamp_to_time, orjson_dumps,

    # 监控埋点
    radar_log,

    # 安全
    create_access_token, get_password_hash, verify_password,
)
```

## 分类索引

### ORM 基类与枚举

| 符号 | 文档 |
|---|---|
| `BaseModel` / `AuditMixin` / `TreeMixin` / `SoftDeleteMixin` | [模型 Mixin](../develop/mixins.md) |
| `StatusType` | 通用 `enable / disable / invalid / all` 枚举 |
| `IntEnum` / `StrEnum` | 业务自定义枚举的基类（带 `get_member_values` / `get_name_by_value`） |

### Schema 基类与响应

详见 [Schema 基类](../develop/schema.md)。

### CRUD

| 符号 | 文档 |
|---|---|
| `CRUDBase` / `get_db_conn` | [CRUDBase](../develop/crud.md) |
| `CRUDRouter` / `SearchFieldConfig` | [CRUDRouter](../develop/crud-router.md) |

### 业务码 & 异常

| 符号 | 用法 |
|---|---|
| `Code.SUCCESS / Code.STATE_TRANSITION_INVALID / ...` | [响应码](./codes.md) |
| `BizError(code, msg)` | 任意层抛出，全局处理器转 `Fail` |
| `SchemaValidationError(code, msg)` | Pydantic 校验器中抛出，绕过 Pydantic 自身的捕获 |

### 鉴权与上下文

详见 [认证 / 鉴权依赖](../develop/auth.md#鉴权依赖)、[认证 / 上下文工具](../develop/auth.md#上下文工具)。

### 数据权限

详见 [数据权限](../develop/data-scope.md)。

### 事件 & 状态机

| 符号 | 文档 |
|---|---|
| `emit(event, **kwargs)` / `on(event)` | [事件总线](../develop/events.md) |
| `StateMachine` | [状态机](../develop/state-machine.md) |

### Sqids & 字段约束

| 符号 | 文档 |
|---|---|
| `SqidId` / `SqidPath` / `encode_id` / `decode_id` | [Sqids 资源 ID](../develop/sqids.md) |
| `Int16` / `Int32` / `Int64` | [Schema 基类 / 字段约束类型](../develop/schema.md#字段约束类型) |

### 配置 & 常量 & 日志

| 符号 | 用法 |
|---|---|
| `APP_SETTINGS` | `APP_SETTINGS.SECRET_KEY / .DB_URL / ...`，详见 [配置](../ops/config.md) |
| `SUPER_ADMIN_ROLE` | `"R_SUPER"` 字符串常量 |
| `log` | Loguru 实例 |

### 监控埋点

```python
from app.utils import radar_log

radar_log("商品状态变更", data={"empId": emp.id, "to": "active"})
radar_log("权限拒绝", level="ERROR", data={...})
```

写入内置 Radar 监控，可在 `/manage/radar/*` 五个页面查看。详见 [监控（Radar）](../ops/radar.md)。

### 安全

| 符号 | 用法 |
|---|---|
| `get_password_hash(plain) -> str` | Argon2 哈希 |
| `verify_password(plain, hashed) -> bool` | 校验 |
| `create_access_token(payload, expires=...) -> str` | 业务自定义 token 时用（一般用不到，登录有 `build_tokens`） |

## 不在 utils 里的东西

| 不导出 | 用途 / 替代方案 |
|---|---|
| `app.core.cache.*` 的具体函数 | 仅供系统层使用；业务自有缓存自己写在模块的 `cache_utils.py` |
| `app.core.redis.*` | Redis 实例直接通过 `request.app.state.redis` 取 |
| `app.core.middlewares.*` | 不建议业务侧加中间件 |
| `app.core.init_app.*` | 框架启动专用 |
| `app.system.models.*` | 业务模块尽量解耦；需要查 User 时建议通过 service 暴露 |

需要时**直接从原路径** import，但请先想清楚是否破坏了"业务不依赖 system 内部"的边界。
