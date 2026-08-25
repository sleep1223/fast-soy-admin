# Authentication

JWT + Argon2 password hashing + Redis-assisted session invalidation. RBAC and row-level data scope are documented separately:

- [RBAC (menus / APIs / buttons)](/en/develop/rbac)
- [Data scope](/en/develop/data-scope)

Source: `app/system/security.py`, `app/system/services/auth.py`, `app/core/dependency.py`.

## JWT settings

| Item | Default | Set via |
|---|---|---|
| Algorithm | HS256 | `JWT_ALGORITHM` |
| Access token | 12 hours | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (minutes) |
| Refresh token | 7 days | `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` (minutes) |
| Signing key | built-in dev value | `SECRET_KEY` (**must change in prod**) |
| Password hash | Argon2 | `app/system/security.py` |

> `SECRET_KEY` is **also** used by `app/core/sqids.py` to derive the alphabet seed. **Rotating SECRET_KEY invalidates all JWTs and all historical sqids at once** — plan a data migration accordingly.

## Token shape

```json
{
  "iat": 1712...,
  "exp": 1712...,
  "data": {
    "userId": 123,
    "userName": "Soybean",
    "tokenType": "accessToken",
    "tokenVersion": 0,
    "impersonatorId": 0
  }
}
```

## Login flow

```
POST /api/v1/auth/login  { userName, password }
   │
   ▼
login_with_credentials()
   ├─ User.filter(user_name=...).first()
   ├─ verify_password(plain, hash)  # Argon2
   ├─ check status_type == enable
   ├─ update_last_login()
   ├─ token_version = redis.get("token_version:{uid}") ?? 0
   └─ build_tokens(user, token_version)
   │
   ▼
return { token, refreshToken, mustChangePassword }
```

### Captcha login / register

`POST /captcha` → backend sends (`send_captcha`), Redis caches for 5 minutes.
`POST /code-login` and `POST /register` both `verify_captcha(redis, phone, code)` first.

### Impersonate

```
POST /api/v1/auth/impersonate/{userId}
  ├─ Only R_SUPER may call (else 2206 SUPER_ADMIN_ONLY)
  └─ build_tokens(target_user, ..., impersonator_id=current_user_id)
```

The issued token carries `impersonatorId`. `/user-info` returns `{"impersonating": true, "impersonatorId": ...}` so the frontend can show "operating as XXX" + an "exit impersonation" button.

## Refresh

```
POST /api/v1/auth/refresh-token  { refreshToken }
   │
   ├─ check_token(refreshToken)  # signature + exp
   ├─ data["tokenType"] == "refreshToken"   else 2105
   ├─ user.status_type == enable             else 2102
   ├─ tokenVersion ≥ redis.token_version    else 2106
   └─ re-issue access + refresh
```

When `access` expires (code `2103`) the frontend interceptor **automatically** calls this endpoint with `refreshToken`, updates local token, and replays the original request.

## Token invalidation (`token_version`)

Password change, account disable, impersonation exit, and admin-forced logout all need to "kill old tokens immediately". Mechanism:

- Each user has a Redis key `token_version:{userId}`, initial `0`
- New tokens carry the current version in the JWT payload
- Every request, `AuthControl.is_authed` compares the token's version with Redis; if smaller, raises `2106 SESSION_INVALIDATED`
- To invalidate, call `invalidate_user_session(redis, user_id)`: `INCR token_version:{user_id}` and old tokens fail on next request

While an account is disabled, requests return `2102 ACCOUNT_DISABLED` first. After it is re-enabled, tokens issued before the disable return `2106 SESSION_INVALIDATED` and never become valid again.

```python
@router.patch("/password", dependencies=[DependAuth])
async def _(body: UpdatePassword, request: Request):
    ...
    await User.filter(id=user_id).update(password=...)
    await invalidate_user_session(request.app.state.redis, user_id)
    return Success(msg="password changed; please log in again")
```

> If Redis is unavailable, the check falls back to "allow + WARNING log" so a Redis outage doesn't kick everyone out.

## Force password change

When `User.must_change_password=True`, `/login` returns `mustChangePassword=true` so the frontend redirects to the change-password page. `PATCH /password` then sets it back to `False`.

Use `ensure_user(..., must_change_password=True)` for seeded accounts (Inventory's auto-created products use this with a random initial password).

## Auth dependencies

### `DependAuth` — auth only

```python
from app.utils import DependAuth

@router.get("/me", dependencies=[DependAuth])
async def me():
    user_id = get_current_user_id()
    ...
```

Steps in `AuthControl.is_authed`:

1. Extract token from `Authorization: Bearer xxx`; missing → `2100`
2. `jwt.decode` (verify exp; expired → `2103`, invalid → `2100`)
3. Check `tokenType == "accessToken"`; else `2101`
4. Load `User`; not enabled / not found → `2102 / 2101`
5. Compare `tokenVersion` with Redis; older → `2106`
6. Load roles / buttons → write into `CTX_USER_ID / CTX_USER / CTX_ROLE_CODES / CTX_BUTTON_CODES`
7. If Redis fails, fall back to a DB query that only loads enabled roles (with WARNING log)

### `DependPermission` — endpoint permission

```python
@router.get("/users/{id}", dependencies=[DependPermission])
```

On top of `DependAuth`:

1. `R_SUPER` passes immediately
2. User has no role → `2207`
3. Aggregate `(method, path, status)` triples across all roles
4. Match `(method.lower(), url.path)` (`check_url` understands `{item_id}`)
5. Hit + `enable` → pass; hit + `disable` → `2200`; no hit → `2201`

Usually mounted on the router group: `router.include_router(..., dependencies=[DependPermission])`.

### `require_buttons(...)` — button permission

```python
from app.utils import require_buttons

@router.post("/products", dependencies=[require_buttons("B_INVENTORY_PRODUCT_CREATE")])
async def _(): ...

# Any one
@router.patch("/x", dependencies=[require_buttons("B_A", "B_B")])

# All required
@router.patch("/y", dependencies=[require_buttons("B_A", "B_B", require_all=True)])
```

Behavior:

- `R_SUPER` always passes
- `require_all=False` (default): any one works; otherwise `2203`
- `require_all=True`: missing any → `2202`

::: tip Pair with CRUDRouter
Use `action_dependencies={"create": [require_buttons(...)]}` to attach in the factory. Applies to `@override` routes too. See [CRUDRouter](/en/develop/crud-router#action_dependencies).
:::

### `require_roles(...)` — role

Same shape as `require_buttons`, codes `2204 / 2205`.

## Context utilities

Per-request ContextVars (`app/core/ctx.py`):

| ContextVar | Type | Available after |
|---|---|---|
| `CTX_USER_ID` | `int \| None` | `DependAuth` |
| `CTX_USER` | `User \| None` | `DependAuth` |
| `CTX_ROLE_CODES` | `list[str]` | `DependAuth` |
| `CTX_BUTTON_CODES` | `list[str]` | `DependAuth` |
| `CTX_IMPERSONATOR_ID` | `int \| None` | impersonate |
| `CTX_X_REQUEST_ID` | `str` | always (middleware) |
| `CTX_BG_TASKS` | `BackgroundTasks \| None` | after `BackgroundTaskMiddleware` |

Helpers:

```python
from app.utils import (
    get_current_user_id,    # int  (raises LookupError if not authed)
    get_current_user,       # User | None
    is_super_admin,         # bool
    has_role_code(code),
    has_button_code(code),
)
```

## Audit — radar_log

```python
from app.utils import radar_log

radar_log("login success", data={"userName": user.user_name, "userId": user.id})
radar_log("permission denied", level="ERROR", data={"method": method, "path": path})
```

With the default `log_to_file=True`, `radar_log` writes sanitized content to Loguru. It is also appended to `radar_user_logs` and shown under `/manage/radar/*` only when the current request is collected by Radar. `/api/v1/auth/**` is never collected, so authentication instrumentation does not enter the Radar tables; with `log_to_file=False` it is not persisted at all. See [Monitoring (Radar)](/en/ops/radar).

## See also

- [RBAC](/en/develop/rbac)
- [Data scope](/en/develop/data-scope)
- [Response codes](/en/reference/codes) — 21xx / 22xx
- [Startup init & reconciliation](/en/develop/init-data) — how roles / menus / APIs get persisted
