# Response Codes

All endpoints return `{"code": "xxxx", "msg": "...", "data": ...}` with HTTP status fixed at 200; the business outcome is carried by `code`.

Source: `app/core/code.py`. The frontend `.env` maps select codes to behaviors (logout / modal logout / auto-refresh / silent fail).

## Code segments

| Range | Meaning |
|---|---|
| `0000` | Success |
| `1000–1999` | System internal error (caught exceptions, validation failure) |
| `2000–2999` | Framework-builtin business errors (auth, permission, conflict, Schema required, etc.) |
| `3000–3999` | Framework-reserved (currently unused) |
| `4000–9999` | Project / business-module codes (module codes **must** start at `4000`; never reuse `2xxx`) |

## 0000 — Success

| Code | Constant | Meaning |
|---|---|---|
| `0000` | `Code.SUCCESS` | Request succeeded |

## 1xxx — System internal

### 10xx — Server errors

| Code | Constant | Meaning |
|---|---|---|
| `1000` | `INTERNAL_ERROR` | Generic / unhandled exception |

### 11xx — Database errors

| Code | Constant | Meaning |
|---|---|---|
| `1100` | `INTEGRITY_ERROR` | Unique / FK constraint violation |
| `1101` | `NOT_FOUND` | Record does not exist (`DoesNotExist`) |

### 12xx — Validation

| Code | Constant | Meaning |
|---|---|---|
| `1200` | `REQUEST_VALIDATION` | Request param / body validation failed (FastAPI layer) |
| `1201` | `RESPONSE_VALIDATION` | Response serialization failed |

> `1200`'s `data.errors` is `[{field, message, type}]`, translated by `_format_validation_error` in `exceptions.py`.

## 2xxx — Business logic

### 21xx — Authentication (frontend has special handling)

| Code | Constant | Meaning | Frontend behavior |
|---|---|---|---|
| `2100` | `INVALID_TOKEN` | Token missing / decode failed / format invalid | Redirect to login |
| `2101` | `INVALID_SESSION` | Wrong token type / user not found | Redirect to login |
| `2102` | `ACCOUNT_DISABLED` | Account disabled | Modal then logout |
| `2103` | `TOKEN_EXPIRED` | Access token expired | Auto-refresh |
| `2104` | `REFRESH_TOKEN_MISSING` | Refresh token missing | — |
| `2105` | `NOT_REFRESH_TOKEN` | Provided token is not a refresh token | — |
| `2106` | `SESSION_INVALIDATED` | `token_version` was incremented; old token invalid | Redirect to login |

> Frontend `.env`: `VITE_SERVICE_LOGOUT_CODES=2100,2101,2104,2105`, `VITE_SERVICE_MODAL_LOGOUT_CODES=2102,2106`, `VITE_SERVICE_EXPIRED_TOKEN_CODES=2103`.

### 22xx — Authorization

| Code | Constant | Meaning |
|---|---|---|
| `2200` | `API_DISABLED` | Endpoint disabled by admin |
| `2201` | `PERMISSION_DENIED` | RBAC API permission denied |
| `2202` | `MISSING_BUTTON_PERMISSION` | `require_buttons(..., require_all=True)` missing some |
| `2203` | `NEED_ANY_BUTTON_PERMISSION` | `require_buttons(...)` missing all |
| `2204` | `MISSING_ROLE` | `require_roles(..., require_all=True)` missing some |
| `2205` | `NEED_ANY_ROLE` | `require_roles(...)` missing all |
| `2206` | `SUPER_ADMIN_ONLY` | Super-admin only |
| `2207` | `USER_NO_ROLE` | User has no role assigned |

### 23xx — Resource conflicts

| Code | Constant | Meaning |
|---|---|---|
| `2300` | `DUPLICATE_RESOURCE` | Generic duplicate (catch-all) |
| `2301` | `DUPLICATE_ROLE_CODE` | Role code exists |
| `2302` | `DUPLICATE_USER_EMAIL` | Email registered |
| `2303` | `DUPLICATE_USER_PHONE` | Phone registered |
| `2304` | `DUPLICATE_USER_NAME` | Username exists |
| `2305` | `DUPLICATE_MENU_ROUTE` | Menu route path exists |

### 24xx — Generic business failure

| Code | Constant | Meaning |
|---|---|---|
| `2400` | `FAIL` | Uncategorized failure (**avoid**; add a specific code) |
| `2401` | `WRONG_CREDENTIALS` | Wrong username / password |
| `2402` | `CAPTCHA_INVALID` | Captcha invalid or expired |
| `2403` | `CAPTCHA_SEND_FAILED` | Captcha send failed |
| `2404` | `PHONE_NOT_REGISTERED` | Phone not registered |
| `2405` | `OLD_PASSWORD_WRONG` | Old password wrong on change-password |
| `2406` | `TARGET_USER_NOT_FOUND` | Target user not found (e.g. impersonate) |
| `2407` | `STATE_TRANSITION_INVALID` | Disallowed state transition |

### 25xx — Rate limit / security

| Code | Constant | Meaning |
|---|---|---|
| `2500` | `RATE_LIMITED` | Too many requests |
| `2501` | `IP_BANNED` | IP temporarily banned |
| `2502` | `ACCESS_DENIED` | Blocked by security policy |

### 26xx — Required field (raised in business schemas)

| Code | Constant | Meaning |
|---|---|---|
| `2600` | `PARAM_REQUIRED` | Generic required (catch-all) |
| `2601` | `USERNAME_REQUIRED` | Username required |
| `2602` | `PASSWORD_REQUIRED` | Password required |
| `2603` | `USER_ROLE_REQUIRED` | User must have at least one role |
| `2604` | `USER_EMAIL_REQUIRED` | User email required |
| `2605` | `ROLE_NAME_REQUIRED` | Role name required |
| `2606` | `ROLE_CODE_REQUIRED` | Role code required |
| `2607` | `ROUTE_NAME_REQUIRED` | Route name required |
| `2608` | `ROUTE_PATH_REQUIRED` | Route path required |

## 4000–9999 — Project-defined

Project-specific codes. The framework doesn't touch them; the frontend doesn't auto-pop errors — handle as you wish.

> Module convention: business module codes must start at `4000` (do **not** occupy the `2xxx` system range). Append your module's range at the end of `app/core/code.py` (e.g. `41xx`, `42xx`). One unique code per failure scenario — never re-use `2400`.

`main` does not define `4xxx` constants for any concrete business module. The `example` branch keeps this HR-specific range:

| Code | Constant | Meaning |
|---|---|---|
| `4000` | `HR_DEPARTMENT_REQUIRED` | A valid department is required when creating an employee |
| `4001` | `HR_MANAGER_REQUIRED` | A department manager is required |
| `4002` | `HR_CREATE_FORBIDDEN` | Employee creation is forbidden |
| `4003` | `HR_TAGS_EXCEED_LIMIT` | Employee tag limit exceeded |
| `4004` | `HR_EMPLOYEE_NOT_IN_DEPT` | Employee is outside the current manager's department |
| `4005` | `HR_USER_NOT_EMPLOYEE` | Current user has no linked employee record |
| `4006` | `HR_MANAGER_ONLY` | The operation is restricted to department managers |
| `4007` | `HR_INVALID_TRANSITION` | Invalid HR employee status transition |

The HR state machine explicitly selects `4007` with `StateMachine(..., error_code=Code.HR_INVALID_TRANSITION)`. Other business modules should allocate their own unique failure codes.

## Raising

```python
from app.utils import BizError, Code, Fail

# A: raise (recommended; transparent across layers)
raise BizError(code=Code.STATE_TRANSITION_INVALID, msg="invalid transition")

# B: return Fail (api layer only; more direct)
return Fail(code=Code.OLD_PASSWORD_WRONG, msg="old password wrong")
```

`SchemaValidationError` (extends `BizError`) is for Pydantic validators: it does **not** extend `ValueError`, so Pydantic won't catch it — it reaches the global handler with the original code.

## Frontend mapping

| Frontend `.env` | Default | Behavior |
|---|---|---|
| `VITE_SERVICE_SUCCESS_CODE` | `0000` | Treat as success, extract `data` |
| `VITE_SERVICE_LOGOUT_CODES` | `2100,2101,2104,2105` | Force logout |
| `VITE_SERVICE_MODAL_LOGOUT_CODES` | `2102,2106` | Modal then logout |
| `VITE_SERVICE_EXPIRED_TOKEN_CODES` | `2103` | Auto-refresh + retry |
| Others | — | Show `msg` as error |
