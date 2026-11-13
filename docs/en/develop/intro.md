# Backend Overview

A layered, modular **FastAPI** backend. Code is split into "system" and "business" modules with strict one-way dependency: business modules are autodiscovered at startup and never import each other.

## Tech stack

| Tech | Purpose |
|------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) ≥ 0.121 | Async web framework |
| [Pydantic v2](https://docs.pydantic.dev/) | Request / response validation & serialization |
| [Tortoise ORM](https://tortoise.github.io) ≥ 1.1 | Async ORM managed through `pyproject.toml` |
| [Tortoise built-in migrations](https://tortoise.github.io/migration.html) | Manual (not auto-run at startup) |
| [Redis](https://redis.io/) | Cache (fastapi-cache2) + multi-worker init lock + RBAC hot data |
| [Argon2](https://argon2-cffi.readthedocs.io/) | Password hashing |
| [PyJWT](https://pyjwt.readthedocs.io/) | JWT |
| [Sqids](https://sqids.org/) | Public-facing resource ID encoding (no exposed auto-increment ints) |
| [Granian](https://github.com/emmett-framework/granian) | ASGI server (with `X-Forwarded-*` proxy reconciliation) |
| Radar (in-house) | Request / SQL / exception dashboard implemented with reference to fastapi-radar; lives under `app/system/radar/` |
| [fastapi-guard](https://fastapi-guard.com/) | Rate limit / auto-ban |
| [Ruff](https://docs.astral.sh/ruff/) | Lint + format (line 200, double-quote) |
| [basedpyright](https://github.com/DetachHead/basedpyright) | Static typing (standard mode) |

## Top-level layout

```
app/
├── __init__.py           # FastAPI app factory, lifespan, multi-worker init coordination
├── core/                 # Framework infrastructure (business uses it via app.utils)
│   ├── autodiscover.py   # business module discovery (models / manifest / api / init_data / standalone DB)
│   ├── base_model.py     # BaseModel / AuditMixin / TreeMixin / enums
│   ├── base_schema.py    # SchemaBase / PageQueryBase / Success / Fail / SuccessExtra
│   ├── code.py           # All response codes
│   ├── config.py         # APP_SETTINGS (pydantic-settings + DB_URL → TORTOISE_ORM)
│   ├── crud.py           # CRUDBase + get_db_conn
│   ├── router.py         # CRUDRouter factory + SearchFieldConfig
│   ├── ctx.py            # ContextVars (CTX_USER_ID / CTX_ROLE_CODES / ...)
│   ├── dependency.py     # DependAuth / DependPermission / require_buttons / require_roles
│   ├── data_scope.py     # row-level data scope
│   ├── cache.py          # Redis cache (role permissions, constant routes, token_version)
│   ├── soft_delete.py    # SoftDeleteMixin (transparent deleted_at IS NULL)
│   ├── sqids.py          # int ↔ sqid string
│   ├── state_machine.py  # lightweight FSM
│   ├── events.py         # in-process event bus (emit/on)
│   ├── exceptions.py     # BizError + global exception handlers
│   ├── middlewares.py    # request id / background tasks / pretty errors
│   └── types.py          # Int16/32/64 / SqidId / SqidPath
├── system/               # Built-in modules (auth, RBAC, users, menus, APIs, dictionary, monitoring)
│   ├── api/              # routes: auth/users/roles/menus/apis/route/dictionary/health
│   ├── controllers/      # CRUDBase subclasses
│   ├── services/         # multi-model orchestration (auth/captcha/user/init_helper/monitor)
│   ├── models/           # admin.py (User/Role/Menu/Api/Button) + dictionary.py
│   ├── schemas/          # admin/users/login/dictionary
│   ├── radar/            # In-house Radar monitoring (request/SQL/exception/instrumentation)
│   ├── security.py       # Argon2 + JWT helpers
│   └── init_data.py      # System menus / roles / users / dictionary seeds
├── business/             # Business modules (autodiscovered)
│   └── <module>/               # example business module created by CLI
├── cli/                  # Code generators (init / gen / gen-web / initdb)
└── utils/                # Stable import facade for business code (re-exports core/system)
```

## Layering

```
HTTP request
    │
    ▼
api/        ← FastAPI routes: thin HTTP adapter, validate + call service/controller + return Success/Fail
    │
    ▼
services/   ← multi-model orchestration, transactions, cache, audit logs, FSM
    │
    ▼
controllers/ ← CRUDBase subclasses, single-resource CRUD + build_search
    │
    ▼
models / schemas
    Tortoise models + Pydantic schemas
```

| Layer | Responsibility | Anti-pattern |
|---|---|---|
| `api/` | URL wiring, dependencies (auth), thin call to service/controller | business rules, cross-model, transactions |
| `services/` | transactions, cross-model, Redis, FSM, audit, cross-module events | HTTP (Request/Response) |
| `controllers/` | `XxxController(CRUDBase)`, `build_search` | multi-model side effects |
| `models/` | columns, indexes, relations, mixins | business validation |
| `schemas/` | `XxxCreate / XxxUpdate / XxxSearch`, field-level validation | cross-resource logic |

## system / business one-way dependency

- `app.system.*` is unaware of `app.business.*`; autodiscover wires up business manifest / legacy routers plus init / policy / event / task slots at startup
- Business modules **must not** reverse-import `app.system.*` (except a few explicitly exposed services) or sibling modules; cross-module talk uses the [event bus](/en/develop/events)
- Business modules import from [`app.utils`](/en/reference/utils) — the stable public surface

## Startup flow

`app/__init__.py` `lifespan`:

1. Init Redis and the fastapi-cache2 backend
2. Clear stale init lock, enter `_run_init_data`:
   - Workers contend for leader via Redis `SET NX EX`; non-leaders wait for `_INIT_DONE_KEY`
   - Leader runs in order: `init_menus` → `refresh_api_list` → `init_users` → each module's `init_data.init()` → `refresh_all_cache`
3. Start Radar and fastapi-guard
4. yield (app ready)
5. Shutdown: stop radar, close Redis

Details: [Startup init & reconciliation](/en/develop/init-data).

## Where to next

- [Architecture](/en/getting-started/architecture) — middleware stack, lifecycle, layer responsibilities
- [Development guide](/en/getting-started/workflow) — build a business module from scratch using the CLI
- [API conventions](/en/develop/api) / [Response codes](/en/reference/codes) — enforced rules
- [Business development](/en/develop/intro) — business module development entry
- [Generic OCR](/en/develop/ocr) — local image text recognition and frontend component
