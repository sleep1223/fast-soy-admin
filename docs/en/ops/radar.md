# Monitoring (Radar / Guard)

Two production-ready monitoring / protection systems:

- **Radar (in-house)** — request / SQL / exception / system-metric tracing with a Web Dashboard, implemented in this project with reference to fastapi-radar; source at `app/system/radar/`.
- **[fastapi-guard](https://fastapi-guard.com/)** — third-party rate limit + auto-ban (anti-scraping / brute force)

Configured in `app/core/config.py` and `app/core/init_app.py`.

## Radar (in-house)

Radar is disabled by default. Once enabled, it captures requests that match its collection rules:

- path, method, status, duration
- every SQL the request executed (parameter count / placeholder information and duration, never bound values)
- exceptions raised
- developer-instrumented logs (`radar_log(...)`)

Data lands in the `radar_requests`, `radar_queries`, and `radar_user_logs` tables in the database selected by `DB_URL`, browsable from the menu "System / Performance":

| Path | Content |
|---|---|
| `/manage/radar/overview` | summary dashboard |
| `/manage/radar/requests` | metadata-only request list; the detail view shows the sanitized full timeline |
| `/manage/radar/queries` | SQL query list (sorted by duration) |
| `/manage/radar/exceptions` | exception list |
| `/manage/radar/monitor` | system metrics (CPU / memory / DB connections) |

### Toggle

```bash
# .env
RADAR_ENABLED=false  # default false; explicitly set true and restart when needed
```

When false, Radar routes and middleware are not mounted, SQL capture is not installed, and the Radar menu seed is disabled. Enabling it and restarting restores the routes, collection, and administrator menu together.

> This project's Radar module is implemented with reference to fastapi-radar.

### Access control

Every `/__radar/api/*` endpoint uses the same Bearer JWT and API RBAC as the main API:

- `R_ADMIN` receives exactly ten request, SQL, exception, statistics, monitoring, and purge endpoints;
- `R_SUPER` keeps the existing super-administrator bypass;
- regular users are denied, while anonymous calls use the existing authentication-failure response;
- the hidden `/__radar/api/_boom` route is not added to the API resource table, remains `R_SUPER`-only, and is still gated by `APP_DEBUG`.

When Radar is enabled, the public API seed for `R_ADMIN` is fixed to:

| Method | Path |
|---|---|
| `GET` | `/__radar/api/requests` |
| `GET` | `/__radar/api/requests/{x_request_id}` |
| `GET` | `/__radar/api/queries` |
| `GET` | `/__radar/api/exceptions` |
| `PUT` | `/__radar/api/exceptions/{x_request_id}/resolve` |
| `GET` | `/__radar/api/stats` |
| `GET` | `/__radar/api/dashboard` |
| `DELETE` | `/__radar/api/purge` |
| `GET` | `/__radar/api/monitor/overview` |
| `GET` | `/__radar/api/monitor/realtime` |

The frontend Radar pages reuse the main request client, including Authorization injection, access-token refresh, and request replay.

### Sensitive-data boundaries

Collection, `radar_log`, database writes, and API responses all use the same `[REDACTED]` sanitizer:

- recursively handles JSON, XML, URL-encoded forms, multipart forms, query strings, sensitive path parameters, and request / response headers;
- masks common password, access / refresh token, Authorization, Cookie / Set-Cookie, API key, secret, CSRF, and OTP variants, plus Bearer and JWT text;
- never captures requests or responses under `/api/v1/auth/**`; `RADAR_INCLUDE_PATHS` cannot override this rule;
- keeps SQL structure for diagnostics while redacting string literals and comments; stores only parameter counts or batch row counts, never bound values;
- omits locals from exception traces; request lists omit headers, bodies, and tracebacks, while details return sanitized content only;
- intentionally preserves ordinary business `code` / `msg` fields so filters and dashboard statistics continue to work. Never place an OTP or another secret in a generic `code` / `msg` field.

Old records are sanitized again when read so historical plaintext is not returned through the Radar API. This does not rewrite plaintext that already exists in the database.

### Handling historical data after upgrade

This fix neither deletes existing Radar data nor changes the database schema. If Radar was enabled on an older public deployment:

1. review reverse-proxy / gateway access logs for `/__radar/api` to assess whether data was read;
2. invalidate potentially exposed tokens and reset passwords, API keys, and other credentials first; if the signing key may be exposed or global invalidation is required, assess the Sqids impact before rotating `SECRET_KEY`;
3. back up the database selected by `DB_URL`, then decide through the incident-response process whether to remove `radar_requests`. Related SQL and user-log rows are cascade-deleted, so this is a destructive operation that requires separate explicit approval.

Radar retention is not enforced automatically. `RADAR_RETENTION_HOURS` is only the default window for an explicit call to the RBAC-protected `DELETE /__radar/api/purge` endpoint. Confirm the backup, scope, and retention policy first.

### radar_log — instrumentation

```python
from app.utils import radar_log

radar_log("login success", data={"userName": "admin", "userId": 1})
radar_log("permission denied", level="ERROR", data={"method": "POST", "path": "/x"})
radar_log("radar only, not file log", log_to_file=False)
```

Args:

| Arg | Default | Meaning |
|---|---|---|
| `message` | — | log body |
| `level` | `"INFO"` | `DEBUG / INFO / WARNING / ERROR / CRITICAL` |
| `data` | `None` | dict, JSON-serialized automatically |
| `log_to_file` | `True` | also log to Loguru file |

An entry is appended to `radar_user_logs` only when the request is inside a Radar collection context. If the request is not collected and `log_to_file=False`, nothing is persisted.

Effect:

- Loguru file log: `<time> | INFO | login success | {"userName": "admin", "userId": 1}`
- Radar Dashboard: appears in the request's "user logs" timeline with caller `module.func:line`

### Recommended use

| Scenario | Use |
|---|---|
| Critical business node (login / state change / payment) | `radar_log` + `data` |
| Permission denial / exception branch | `radar_log(level="ERROR", data=...)` |
| High-volume debug | `log.debug(...)`, not radar |
| Auto-captured request / SQL | radar already does it; don't duplicate |

## [fastapi-guard](https://fastapi-guard.com/)

Third-party per-request rate limit + auto-ban.

```bash
# .env
GUARD_ENABLED=true             # default true
GUARD_RATE_LIMIT=100           # requests per window
GUARD_RATE_LIMIT_WINDOW=60     # window size (seconds)
GUARD_AUTO_BAN_THRESHOLD=10    # violations before auto-ban
GUARD_AUTO_BAN_DURATION=21600  # ban duration (seconds, 6 hours)
```

Returns:

| Code | Meaning |
|---|---|
| `2500 RATE_LIMITED` | too many requests |
| `2501 IP_BANNED` | IP auto-banned |
| `2502 ACCESS_DENIED` | blocked by security policy |

### Behind a reverse proxy

Enable `PROXY_HEADERS_ENABLED=true` so granian reconciles `X-Forwarded-For` / `X-Forwarded-Proto` to the real client IP — guard relies on this. **Production behind Nginx must enable**, otherwise every request looks like the nginx container's IP and triggers blanket bans.

```bash
PROXY_HEADERS_ENABLED=true
TRUSTED_HOSTS=["127.0.0.1", "10.0.0.0/8"]  # trusted upstreams
```

### Banned — what to do

```bash
# Nuke guard's Redis counters / ban list
redis-cli --scan --pattern "fastapi_guard:*" | xargs redis-cli del
```

Or temporarily set `GUARD_ENABLED=false` and restart.

## Logging (Loguru)

- Configured in `app/core/log.py`
- Output dir: `logs/` (set by `APP_SETTINGS.LOGS_ROOT`)
- Retention: `LOG_INFO_RETENTION="30 days"` (supports `seconds/minutes/hours/days/weeks/months/years`)

In business code:

```python
from app.utils import log

log.info("..."); log.warning("..."); log.error("..."); log.exception("...")
```

`radar_log` calls Loguru internally — **don't** double-log.

## guard_core noise suppression

[fastapi-guard](https://fastapi-guard.com/)'s internal `guard_core` library installs its own StreamHandler with verbose INFO output. `create_app` clears its handlers and bumps the level to WARNING so business logs aren't drowned.

## See also

- [Auth / radar_log usage](/en/develop/auth#audit--radar_log)
- [Configuration](/en/ops/config) — RADAR / GUARD / PROXY env vars
