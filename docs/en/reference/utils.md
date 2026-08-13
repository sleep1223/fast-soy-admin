# app.utils — business import facade

`app/utils/__init__.py` re-exports the symbols business modules use most often, so business code never needs `from app.core.xxx import ...` / `from app.system.xxx import ...` everywhere.

::: tip Strong rule
Business modules (`app/business/<x>/`) import via `app.utils` only. Inside `app/system/`, to avoid circular deps, keep importing `app/core/*` directly.
:::

## One-line import cheat sheet

```python
from app.utils import (
    # ORM bases & enums
    BaseModel, AuditMixin, TreeMixin, SoftDeleteMixin,
    StatusType, IntEnum, StrEnum,

    # Schema bases & response wrappers
    SchemaBase, PageQueryBase,
    Success, Fail, SuccessExtra,
    CommonIds, OfflineByRoleRequest,
    ResponseModel, PageResponseModel,
    Custom, make_optional,

    # CRUD
    CRUDBase, get_db_conn,
    CRUDRouter, SearchFieldConfig,

    # Business code & exceptions
    Code, BizError, SchemaValidationError,

    # Auth & context
    DependAuth, DependPermission,
    require_buttons, require_roles,
    CTX_USER_ID,
    get_current_user, get_current_user_id,
    is_super_admin, has_role_code, has_button_code,

    # Data scope
    DataScopeType, build_scope_filter,

    # Events & state machine
    emit, on,
    StateMachine,

    # Sqids & field constraints
    encode_id, decode_id,
    SqidId, SqidPath,
    Int16, Int32, Int64,

    # Config & constants & log
    APP_SETTINGS, SUPER_ADMIN_ROLE, log,

    # Utilities
    camel_case_convert, snake_case_convert,
    to_camel_case, to_snake_case,
    to_lower_camel_case, to_upper_camel_case,
    time_to_timestamp, timestamp_to_time, orjson_dumps,

    # Monitoring
    radar_log,

    # Security
    create_access_token, get_password_hash, verify_password,
)
```

## Categorized index

### ORM bases & enums

| Symbol | Doc |
|---|---|
| `BaseModel` / `AuditMixin` / `TreeMixin` / `SoftDeleteMixin` | [Mixins](/en/develop/mixins) |
| `StatusType` | generic `enable / disable / invalid / all` enum |
| `IntEnum` / `StrEnum` | base for custom business enums (with `get_member_values` / `get_name_by_value`) |

### Schema bases & response

See [Schema base](/en/develop/schema).

### CRUD

| Symbol | Doc |
|---|---|
| `CRUDBase` / `get_db_conn` | [CRUDBase](/en/develop/crud) |
| `CRUDRouter` / `SearchFieldConfig` | [CRUDRouter](/en/develop/crud-router) |

### Business code & exceptions

| Symbol | Use |
|---|---|
| `Code.SUCCESS / Code.STATE_TRANSITION_INVALID / ...` | [Response codes](/en/reference/codes) |
| `BizError(code, msg)` | raise from any layer; global handler returns `Fail` |
| `SchemaValidationError(code, msg)` | raise inside Pydantic validators (bypasses Pydantic's own catch) |

### Auth & context

See [Auth / dependencies](/en/develop/auth#auth-dependencies) and [Auth / context utilities](/en/develop/auth#context-utilities).

### Data scope

See [Data scope](/en/develop/data-scope).

### Events & state machine

| Symbol | Doc |
|---|---|
| `emit(event, **kwargs)` / `on(event)` | [Event bus](/en/develop/events) |
| `StateMachine` | [State machine](/en/develop/state-machine) |

### Sqids & constraints

| Symbol | Doc |
|---|---|
| `SqidId` / `SqidPath` / `encode_id` / `decode_id` | [Sqids](/en/develop/sqids) |
| `Int16` / `Int32` / `Int64` | [Schema / constraint types](/en/develop/schema#field-constraint-types) |

### Config & constants & log

| Symbol | Use |
|---|---|
| `APP_SETTINGS` | `APP_SETTINGS.SECRET_KEY / .DB_URL / ...`, see [Configuration](/en/ops/config) |
| `SUPER_ADMIN_ROLE` | string `"R_SUPER"` |
| `log` | Loguru instance |

### Monitoring

```python
from app.utils import radar_log

radar_log("product state changed", data={"empId": emp.id, "to": "active"})
radar_log("permission denied", level="ERROR", data={...})
```

Writes to the in-house Radar monitoring; visible at `/manage/radar/*`. See [Monitoring (Radar)](/en/ops/radar).

### Security

| Symbol | Use |
|---|---|
| `get_password_hash(plain) -> str` | Argon2 hash |
| `verify_password(plain, hashed) -> bool` | verify |
| `create_access_token(payload, expires=...) -> str` | for custom tokens (login uses `build_tokens`) |

## Not exported

| Not exported | Why / alternative |
|---|---|
| Specific functions in `app.core.cache.*` | system-only; business writes its own `cache_utils.py` |
| `app.core.redis.*` | get the Redis instance from `request.app.state.redis` |
| `app.core.middlewares.*` | business shouldn't add middleware |
| `app.core.init_app.*` | framework startup only |
| `app.system.models.*` | keep modules decoupled; expose via system services if needed |

If you do need them, **import from the source path directly** — but reconsider whether you're breaking the "business doesn't depend on system internals" boundary.
