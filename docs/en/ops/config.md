# Configuration

The backend reads `.env` from the project root via Pydantic Settings (`app/core/config.py`). The frontend reads `web/.env` via Vite.

## Backend `.env`

::: code-group
```dotenv [development]
# ---- App ----
APP_TITLE=FastSoyAdmin
APP_DEBUG=true
SECRET_KEY=015a42020f023ac2c3eda3d45fe5ca3fef8921ce63589f6d4fcdef9814cd7fa7

# ---- CORS ----
CORS_ORIGINS=["http://localhost:9527"]

# ---- DB ----
DB_URL=postgres://postgres:password@localhost:5432/fastsoyadmin

# ---- Redis ----
REDIS_URL=redis://localhost:6379/0

# ---- JWT ----
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=720         # 12 hours
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080      # 7 days

# ---- Monitoring ----
# Disabled by default; opt in only after reviewing the collection scope
RADAR_ENABLED=false

# ---- Rate limit (fastapi-guard, https://fastapi-guard.com/) ----
GUARD_ENABLED=true
GUARD_RATE_LIMIT=100
GUARD_RATE_LIMIT_WINDOW=60
GUARD_AUTO_BAN_THRESHOLD=10
GUARD_AUTO_BAN_DURATION=21600

# ---- Reverse-proxy header reconciliation ----
PROXY_HEADERS_ENABLED=false
TRUSTED_HOSTS=["127.0.0.1"]

# ---- Logging ----
LOG_INFO_RETENTION=30 days
```

```dotenv [production diffs]
APP_DEBUG=false
SECRET_KEY=<generate a fresh 256-bit random>

CORS_ORIGINS=["https://your-admin.example.com"]

DB_URL=postgres://user:pwd@db:5432/fastsoyadmin?maxsize=50&minsize=5

REDIS_URL=redis://:strong-password@redis:6379/0

# Required behind Nginx / a gateway
PROXY_HEADERS_ENABLED=true
TRUSTED_HOSTS=["10.0.0.0/8"]
```
:::

## All settings

| Setting | Default | Purpose |
|---|---|---|
| `VERSION` | `0.1.0` | application version (affects OpenAPI) |
| `APP_TITLE` | `FastSoyAdmin` | OpenAPI title |
| `APP_DESCRIPTION` | `Description` | OpenAPI description |
| `APP_DEBUG` | `false` | enables `/openapi.json` + Swagger UI |
| `SECRET_KEY` | dev built-in | JWT signing key + Sqids alphabet seed (**must change in prod**) |
| `CORS_ORIGINS` | `["*"]` | allowed origins |
| `CORS_ALLOW_CREDENTIALS` | `true` | — |
| `CORS_ALLOW_METHODS` | `["*"]` | — |
| `CORS_ALLOW_HEADERS` | `["*"]` | — |
| `DB_URL` | `postgres://postgres:password@localhost:5432/fastsoyadmin` | Tortoise URL; see [Switching DB](/en/ops/database) for SQLite/MySQL/MSSQL/Oracle |
| `TORTOISE_ORM` | auto-built | **don't set manually**; multi-line JSON in `.env` is fragile |
| `REDIS_URL` | `redis://redis:6379/0` | Redis URL |
| `JWT_ALGORITHM` | `HS256` | — |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | access token lifetime (minutes) |
| `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | refresh token lifetime (minutes) |
| `DATETIME_FORMAT` | `"%Y-%m-%d %H:%M:%S"` | format for `to_dict`'s `fmtCreatedAt` etc. |
| `RADAR_ENABLED` | `false` | enable in-house Radar monitoring; after restart only `R_ADMIN` / `R_SUPER` may access it, and auth endpoints are never collected |
| `RADAR_RETENTION_HOURS` | `24` | default retention window for an explicit Radar purge call; no automatic cleanup runs |
| `GUARD_ENABLED` | `true` | enable [fastapi-guard](https://fastapi-guard.com/) rate limiting |
| `GUARD_RATE_LIMIT` | `100` | requests allowed per window |
| `GUARD_RATE_LIMIT_WINDOW` | `60` | window size (seconds) |
| `GUARD_AUTO_BAN_THRESHOLD` | `10` | violations before auto-ban |
| `GUARD_AUTO_BAN_DURATION` | `21600` | auto-ban duration (seconds; default 6h) |
| `PROXY_HEADERS_ENABLED` | `false` | reconcile `X-Forwarded-*` to true client IP |
| `TRUSTED_HOSTS` | `["127.0.0.1"]` | trusted upstream list (IP / CIDR) |
| `LOG_INFO_RETENTION` | `30 days` | controls Loguru file retention only, not Radar tables; supports `seconds/minutes/hours/days/weeks/months/years` |
| `PROJECT_ROOT` | parent of `app/` | auto-derived |
| `BASE_DIR` | `PROJECT_ROOT.parent` | auto-derived |
| `LOGS_ROOT` | `BASE_DIR / "logs/"` | mkdir at startup |
| `STATIC_ROOT` | `BASE_DIR / "static/"` | mkdir at startup |

### Business endpoint rate limits

Global rate limiting is still controlled by `GUARD_RATE_LIMIT` / `GUARD_RATE_LIMIT_WINDOW`. For a stricter business endpoint limit, declare this in a business API module:

```python
ENDPOINT_RATE_LIMITS = {
    "/api/v1/business/inventory/products/search": (30, 60),
}
```

At startup, `discover_business_endpoint_rate_limits()` auto-merges these entries into fastapi-guard. The CLI can generate this declaration too:

```bash
uv run python -m app.cli crud inventory --models Product --rate-limit Product:30/60
```

## Module-local config

A business module can declare its own Settings in `app/business/<name>/config.py`:

```python
# app/business/inventory/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class InventorySettings(BaseSettings):
    INVENTORY_TAG_PER_PRODUCT_LIMIT: int = 5
    DB_URL: str | None = None              # if different from main, autodiscover registers a separate connection

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="INVENTORY_")

BIZ_SETTINGS = InventorySettings()
```

`env_prefix` carves out a namespace: in `.env` use `INVENTORY_TAG_PER_PRODUCT_LIMIT=8`, `INVENTORY_DB_URL=postgres://...`.

Business code:

```python
from app.business.inventory.config import BIZ_SETTINGS
limit = BIZ_SETTINGS.INVENTORY_TAG_PER_PRODUCT_LIMIT
```

For standalone DB behavior see [Autodiscover / standalone DB](/en/develop/autodiscover#business-module-standalone-database).

## Frontend `.env`

```dotenv
# web/.env

VITE_AUTH_ROUTE_MODE=dynamic
VITE_ROUTE_HOME=home

VITE_SERVICE_SUCCESS_CODE=0000
VITE_SERVICE_LOGOUT_CODES=2100,2101,2104,2105
VITE_SERVICE_MODAL_LOGOUT_CODES=2102,2106
VITE_SERVICE_EXPIRED_TOKEN_CODES=2103

VITE_SERVICE_BASE_URL=/api/v1
VITE_OTHER_SERVICE_BASE_URL={"demo": "/demo"}

VITE_ICON_PREFIX=icon
VITE_ICON_LOCAL_PREFIX=icon-local
```

See [Frontend / Request / intro](/en/frontend/request/intro).

## Code style

- `ruff.toml`: line 200, double-quote, sorted imports, rules E/F/I
- basedpyright: standard mode, target `app/` (config in `pyproject.toml` `[tool.basedpyright]`)
- Frontend ESLint: `@soybeanjs/eslint-config-vue`

See [Commands](/en/reference/commands) and [Backend style](/en/standard/backend).

## Rotating SECRET_KEY

`SECRET_KEY` is used for two things:

1. JWT HMAC signing → rotation **invalidates all existing JWTs** (everyone re-logs in)
2. Sqids alphabet seed → rotation **invalidates all historical sqids** (external links / bookmarks / integrations break)

If you must rotate in production:

- announce + give external integrations time to migrate
- bump an API version
- keep the old SECRET_KEY around for "dual signing" temporarily (custom code required)

See [Sqids / rotating SECRET_KEY](/en/develop/sqids#rotating-secret_key).

## See also

- [Switching DB](/en/ops/database) — full `DB_URL` syntax
- [Deployment](/en/ops/deployment) — Nginx / Docker / proxy
- [Monitoring](/en/ops/radar) — RADAR / GUARD details
