# 配置

后端通过 Pydantic Settings 读取根目录的 `.env`（[`app/core/config.py`](../../../app/core/config.py)）。前端通过 Vite 读取 `web/.env`。

## 后端 .env

::: code-group
```dotenv [示例：开发环境]
# ---- 应用 ----
APP_TITLE=FastSoyAdmin
APP_DEBUG=true
SECRET_KEY=015a42020f023ac2c3eda3d45fe5ca3fef8921ce63589f6d4fcdef9814cd7fa7

# ---- CORS ----
CORS_ORIGINS=["http://localhost:9527"]

# ---- 数据库 ----
DB_URL=postgres://postgres:password@localhost:5432/fastsoyadmin

# ---- Redis ----
REDIS_URL=redis://localhost:6379/0

# ---- JWT ----
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=720         # 12 小时
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080      # 7 天

# ---- 监控 ----
# 默认关闭；仅在确认需要且已了解采集范围后显式开启
RADAR_ENABLED=false

# ---- 限流（fastapi-guard, https://fastapi-guard.com/） ----
GUARD_ENABLED=true
GUARD_RATE_LIMIT=100
GUARD_RATE_LIMIT_WINDOW=60
GUARD_AUTO_BAN_THRESHOLD=10
GUARD_AUTO_BAN_DURATION=21600

# ---- 反代头还原 ----
PROXY_HEADERS_ENABLED=false
TRUSTED_HOSTS=["127.0.0.1"]

# ---- 日志 ----
LOG_INFO_RETENTION=30 days
```

```dotenv [生产环境关键差异]
APP_DEBUG=false
SECRET_KEY=<请生成新的 256-bit 随机串>

CORS_ORIGINS=["https://your-admin.example.com"]

DB_URL=postgres://user:pwd@db:5432/fastsoyadmin?maxsize=50&minsize=5

REDIS_URL=redis://:strong-password@redis:6379/0

# 部署在 Nginx / 网关之后必须开启
PROXY_HEADERS_ENABLED=true
TRUSTED_HOSTS=["10.0.0.0/8"]
```
:::

## 全部配置项

| 配置 | 默认 | 说明 |
|---|---|---|
| `VERSION` | `0.1.0` | 应用版本号（影响 OpenAPI） |
| `APP_TITLE` | `FastSoyAdmin` | OpenAPI title |
| `APP_DESCRIPTION` | `Description` | OpenAPI description |
| `APP_DEBUG` | `false` | `true` 时启用 `/openapi.json` 与 Swagger UI |
| `SECRET_KEY` | 内置开发用 | JWT 签名 + Sqids 字母表种子（**生产必须改**） |
| `CORS_ORIGINS` | `["*"]` | 允许跨域的来源列表 |
| `CORS_ALLOW_CREDENTIALS` | `true` | — |
| `CORS_ALLOW_METHODS` | `["*"]` | — |
| `CORS_ALLOW_HEADERS` | `["*"]` | — |
| `DB_URL` | `postgres://postgres:password@localhost:5432/fastsoyadmin` | Tortoise URL，详见 [切换数据库](./database.md)；SQLite 写法见该文档 |
| `TORTOISE_ORM` | 自动构建 | **不要手动设置**，会破坏多行 JSON 的 .env 解析 |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 连接 URL |
| `JWT_ALGORITHM` | `HS256` | — |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | access token 有效期（分钟） |
| `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | refresh token 有效期（分钟） |
| `DATETIME_FORMAT` | `"%Y-%m-%d %H:%M:%S"` | `to_dict` 输出 `fmtCreatedAt` 等格式化字段时使用 |
| `RADAR_ENABLED` | `false` | 启用内置 Radar 监控；开启并重启后仅 `R_ADMIN` / `R_SUPER` 可访问，认证端点永不采集 |
| `RADAR_RETENTION_HOURS` | `24` | 手工调用 Radar purge 接口时的默认保留时长；系统不会自动清理 |
| `GUARD_ENABLED` | `true` | 启用 [fastapi-guard](https://fastapi-guard.com/) 限流 |
| `GUARD_RATE_LIMIT` | `100` | 每窗口内允许请求数 |
| `GUARD_RATE_LIMIT_WINDOW` | `60` | 限流窗口大小（秒） |
| `GUARD_AUTO_BAN_THRESHOLD` | `10` | 触发自动封禁的违规次数 |
| `GUARD_AUTO_BAN_DURATION` | `21600` | 自动封禁时长（秒，默认 6 小时） |
| `PROXY_HEADERS_ENABLED` | `false` | 是否从 `X-Forwarded-*` 还原真实客户端 IP |
| `TRUSTED_HOSTS` | `["127.0.0.1"]` | 信任的上游列表（IP / CIDR） |
| `LOG_INFO_RETENTION` | `30 days` | 仅控制 Loguru 文件日志保留时间，不清理 Radar 表；支持 `seconds/minutes/hours/days/weeks/months/years` |
| `PROJECT_ROOT` | `app/` 父目录 | 自动推导 |
| `BASE_DIR` | `PROJECT_ROOT.parent` | 自动推导 |
| `LOGS_ROOT` | `BASE_DIR / "logs/"` | 启动时自动 mkdir |
| `STATIC_ROOT` | `BASE_DIR / "static/"` | 启动时自动 mkdir |

### 业务端点限流

全局限流仍由 `GUARD_RATE_LIMIT` / `GUARD_RATE_LIMIT_WINDOW` 控制。需要给某个业务列表接口配置更严格的端点限流时，可在业务 API 模块声明：

```python
ENDPOINT_RATE_LIMITS = {
    "/api/v1/business/inventory/products/search": (30, 60),
}
```

启动时 `discover_business_endpoint_rate_limits()` 会自动合并这些配置到 fastapi-guard。CLI 也可以生成该声明：

```bash
uv run python -m app.cli crud inventory --models Product --rate-limit Product:30/60
```

## 业务模块自有配置

业务模块在 `app/business/<name>/config.py` 声明自己的 Settings：

```python
# app/business/inventory/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class InventorySettings(BaseSettings):
    INVENTORY_TAG_PER_PRODUCT_LIMIT: int = 5
    DB_URL: str | None = None              # 若与主库不同，autodiscover 注册独立连接

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="INVENTORY_")

BIZ_SETTINGS = InventorySettings()
```

通过 `env_prefix` 隔离命名空间：`.env` 中用 `INVENTORY_TAG_PER_PRODUCT_LIMIT=8`、`INVENTORY_DB_URL=postgres://...` 覆盖。

业务代码：

```python
from app.business.inventory.config import BIZ_SETTINGS
limit = BIZ_SETTINGS.INVENTORY_TAG_PER_PRODUCT_LIMIT
```

模块独立 DB 行为详见 [自动发现 / 业务模块独立数据库](../develop/autodiscover.md#业务模块独立数据库)。

## 前端 .env

```dotenv
# web/.env

# 路由模式：dynamic = 后端下发动态路由
VITE_AUTH_ROUTE_MODE=dynamic
VITE_ROUTE_HOME=home

# 后端响应码映射
VITE_SERVICE_SUCCESS_CODE=0000
VITE_SERVICE_LOGOUT_CODES=2100,2101,2104,2105
VITE_SERVICE_MODAL_LOGOUT_CODES=2102,2106
VITE_SERVICE_EXPIRED_TOKEN_CODES=2103

# 服务地址
VITE_SERVICE_BASE_URL=/api/v1
VITE_OTHER_SERVICE_BASE_URL={"demo": "/demo"}

# 图标前缀
VITE_ICON_PREFIX=icon
VITE_ICON_LOCAL_PREFIX=icon-local
```

详见 [前端 / 请求 / 简介](../frontend/request/intro.md)。

## 代码风格

- `ruff.toml`：行宽 200，规则 E/F/I，双引号
- basedpyright：standard 模式，检查 `app/`（配置在 `pyproject.toml` 的 `[tool.basedpyright]`）
- 前端 ESLint 基于 `@soybeanjs/eslint-config-vue`

详细命令见 [命令参考](../reference/commands.md) 与 [规范 / 后端](../standard/backend.md)。

## SECRET_KEY 轮换

`SECRET_KEY` 用作两件事：

1. JWT HMAC 签名 → 轮换后**所有现有 JWT 立刻无法验签**，全员需要重新登录
2. Sqids 字母表种子 → 轮换后**所有历史 sqid 全部失效**，外部持有的链接 / 收藏 / 集成方都会失效

如果生产必须轮换：

- 提前公告 + 让外部集成方做兼容
- 升一个 API 版本号
- 后台保留旧 SECRET_KEY 一段时间做"双签"是可行的（需要业务侧自实现 fallback 逻辑）

详见 [Sqids / 轮换 SECRET_KEY 怎么办](../develop/sqids.md#轮换-secret_key-怎么办)。

## 相关

- [切换数据库](./database.md) — `DB_URL` 详细语法
- [部署](./deployment.md) — Nginx / Docker / 反代配置
- [监控](./radar.md) — RADAR / GUARD 详细行为
