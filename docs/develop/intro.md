# 后端简介

基于 **FastAPI** 的分层模块化后端。代码分"系统模块"和"业务模块"两类，业务模块自动发现注册，禁止反向依赖。

## 技术栈

| 技术 | 说明 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) ≥ 0.121 | 异步 Web 框架 |
| [Pydantic v2](https://docs.pydantic.dev/) | 请求/响应校验与序列化 |
| [Tortoise ORM](https://tortoise.github.io) ≥ 1.1 | 异步 ORM（通过 `pyproject.toml` 管理依赖） |
| [Tortoise 内置迁移](https://tortoise.github.io/migration.html) | 手动执行（不在启动时自动迁移） |
| [Redis](https://redis.io/) | 缓存（fastapi-cache2）+ 多 worker 启动锁 + 角色权限热数据 |
| [Argon2](https://argon2-cffi.readthedocs.io/) | 密码哈希 |
| [PyJWT](https://pyjwt.readthedocs.io/) | JWT 令牌 |
| [Sqids](https://sqids.org/) | 资源 ID 编码（对外不暴露自增 int） |
| [Granian](https://github.com/emmett-framework/granian) | ASGI 服务器（含反代 X-Forwarded-* 还原） |
| Radar（内置） | 参考 fastapi-radar 实现的请求/SQL/异常 Dashboard，位于 `app/system/radar/` |
| [fastapi-guard](https://fastapi-guard.com/) | 限流 / 自动封禁 |
| [Ruff](https://docs.astral.sh/ruff/) | Lint + format（行宽 200，双引号） |
| [basedpyright](https://github.com/DetachHead/basedpyright) | 静态类型检查（standard 模式） |

## 顶层目录

```
app/
├── __init__.py           # FastAPI 应用工厂、lifespan、多 worker init 协调
├── core/                 # 框架基础设施（业务模块通过 app.utils 间接使用）
│   ├── autodiscover.py   # 业务模块发现（models/manifest/api/init_data/独立 DB）
│   ├── base_model.py     # BaseModel / AuditMixin / TreeMixin / 枚举
│   ├── base_schema.py    # SchemaBase / PageQueryBase / Success / Fail / SuccessExtra
│   ├── code.py           # 全应用响应码
│   ├── config.py         # APP_SETTINGS（pydantic-settings + DB_URL → TORTOISE_ORM）
│   ├── crud.py           # CRUDBase + get_db_conn
│   ├── router.py         # CRUDRouter 工厂 + SearchFieldConfig
│   ├── ctx.py            # ContextVars（CTX_USER_ID / CTX_ROLE_CODES / ...）
│   ├── dependency.py     # DependAuth / DependPermission / require_buttons / require_roles
│   ├── data_scope.py     # 行级数据权限
│   ├── cache.py          # Redis 缓存（角色权限、常量路由、token_version）
│   ├── soft_delete.py    # SoftDeleteMixin（透明 deleted_at IS NULL）
│   ├── sqids.py          # int ↔ sqid 字符串
│   ├── state_machine.py  # 轻量状态机
│   ├── events.py         # 进程内事件总线（emit/on）
│   ├── exceptions.py     # BizError + 全局异常处理器
│   ├── middlewares.py    # 请求 ID / 后台任务 / 异常美化
│   └── types.py          # Int16/32/64 / SqidId / SqidPath
├── system/               # 系统模块（认证、RBAC、用户、菜单、API、字典、监控）
│   ├── api/              # 路由：auth/users/roles/menus/apis/route/dictionary/health
│   ├── controllers/      # CRUDBase 子类
│   ├── services/         # 多模型编排（auth/captcha/user/init_helper/monitor）
│   ├── models/           # admin.py（User/Role/Menu/Api/Button） + dictionary.py
│   ├── schemas/          # admin/users/login/dictionary
│   ├── radar/            # 内置 Radar 监控（请求/SQL/异常/埋点 Dashboard）
│   ├── security.py       # Argon2 + JWT 工具
│   └── init_data.py      # 系统菜单/角色/用户/字典种子
├── business/             # 业务模块（autodiscover 自动加载）
│   └── <module>/               # 业务模块示例：由 CLI 创建
├── cli/                  # 代码生成器（init / gen / gen-web / initdb）
└── utils/                # 业务开发者的统一导入入口（重新导出 core/system 常用符号）
```

## 分层

```
HTTP Request
    │
    ▼
api/        ← FastAPI 路由：薄 HTTP 适配器，校验 + 调 service/controller + Success/Fail
    │
    ▼
services/   ← 多模型编排、事务、缓存、审计日志、状态机
    │
    ▼
controllers/ ← CRUDBase 子类，单资源 CRUD 与 build_search
    │
    ▼
models / schemas
    Tortoise ORM 模型 + Pydantic Schema
```

| 层 | 写什么 | 不写什么 |
|---|---|---|
| `api/` | URL 接线、依赖（鉴权）、调 service/controller 的薄包装 | 业务规则、跨模型、事务 |
| `services/` | 事务、跨模型、Redis、状态机、审计、跨模块事件 | HTTP（Request/Response） |
| `controllers/` | `XxxController(CRUDBase)`、`build_search`；单模型 CRUD | 跨模型编排、事务、缓存、事件派发、外部 IO |
| `models/` | 表字段、索引、关系、Mixin | 业务校验 |
| `schemas/` | `XxxCreate / XxxUpdate / XxxSearch`，字段级校验 | 跨资源 |

## system / business 单向依赖

- `app.system.*` 不感知 `app.business.*`，仅启动时由 `autodiscover` 挂载业务 manifest / legacy router，并调用 init / policy / event / task 插槽
- 业务模块**禁止**反向 import `app.system.*`，**禁止**互相 import；跨模块用[事件总线](./events.md)
- 业务模块统一从 [`app.utils`](../reference/utils.md) 导入，这是稳定对外入口

## 启动流程

`app/__init__.py` 的 `lifespan`：

1. 初始化 Redis 与 fastapi-cache2
2. 清理上次的 init 锁，进入 `_run_init_data`：
   - 多 worker 通过 `SET NX EX` 抢 leader，非 leader 等待 `_INIT_DONE_KEY`
   - leader 顺序执行：`init_menus` → `refresh_api_list` → `init_users` → 各业务模块 `init_data.init()` → `refresh_all_cache`
3. 启动 Radar 与 fastapi-guard
4. yield（应用就绪）
5. 关闭：shutdown radar、关闭 Redis

详细同步语义见 [启动初始化与对账](./init-data.md)。

## 接下来读什么

- [架构](../getting-started/architecture.md) — 中间件栈、生命周期、目录到职责的映射
- [开发指南](../getting-started/workflow.md) — 用 CLI 从 0 搭一个业务模块
- [API 约定](./api.md) / [响应码](../reference/codes.md) — 强制约定
- [业务开发](intro.md) — 业务模块开发入口
- [通用 OCR](./ocr.md) — 本地图片文字识别与前端组件
