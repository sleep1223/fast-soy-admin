# 监控（Radar / Guard）

后端内置两套生产可用的监控/防护：

- **Radar（内置）** — 参考 fastapi-radar 实现的请求 / SQL 查询 / 异常 / 系统指标 全栈追踪（含一个 Web Dashboard），源码位于 [`app/system/radar/`](../../../app/system/radar/)
- **[fastapi-guard](https://fastapi-guard.com/)** — 第三方限流 + 自动封禁（防爬虫 / 暴力破解）

配置在 [`app/core/config.py`](../../../app/core/config.py) 与 [`app/core/init_app.py`](../../../app/core/init_app.py)。

## Radar（内置）

Radar 默认关闭。启用后，它会捕获符合采集规则的请求：

- 请求路径、方法、状态码、耗时
- 该请求执行的所有 SQL（只保留参数数量 / 占位信息与耗时，不保存绑定参数值）
- 该请求触发的异常
- 业务侧主动埋的日志（`radar_log(...)`）

数据写入 `DB_URL` 对应数据库的 `radar_requests`、`radar_queries`、`radar_user_logs` 表，通过菜单"系统管理 / 性能监控"下五个页面查看：

| 路径 | 内容 |
|---|---|
| `/manage/radar/overview` | 总览仪表板 |
| `/manage/radar/requests` | 请求列表仅显示元数据；详情页显示脱敏后的完整时间线 |
| `/manage/radar/queries` | SQL 查询列表（按耗时排序） |
| `/manage/radar/exceptions` | 异常列表 |
| `/manage/radar/monitor` | 系统指标（CPU / 内存 / DB 连接数） |

### 启用 / 关闭

```bash
# .env
RADAR_ENABLED=false  # 默认 false；需要时显式改为 true 并重启
```

关闭后不会挂载 Radar 路由和采集中间件，也不会安装 SQL 捕获，Radar 菜单种子会被置为禁用。启用并重启后，路由、采集和管理员菜单一起恢复。

> 本项目参考 fastapi-radar 实现。

### 访问控制

`/__radar/api/*` 使用与主 API 相同的 Bearer JWT 和 API RBAC：

- `R_ADMIN` 默认获得 10 个请求、SQL、异常、统计、监控和清理接口；
- `R_SUPER` 沿用超级管理员自动放行；
- 普通用户无权访问；未登录请求会按现有认证失败响应返回；
- 隐藏的 `/__radar/api/_boom` 不进入 API 资源表，只允许 `R_SUPER` 使用，并仍受 `APP_DEBUG` 限制。

启用 Radar 时，`R_ADMIN` 的公开 API 种子固定为：

| 方法 | 路径 |
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

前端 Radar 页面复用主请求客户端，因此会自动携带 Authorization，并沿用 access token 过期刷新与请求重放逻辑。

### 敏感数据边界

采集、`radar_log`、数据库写入和 API 返回都会使用统一的 `[REDACTED]` 脱敏器：

- 递归处理 JSON、XML、URL 编码表单、multipart 表单、查询字符串、敏感路径参数以及请求 / 响应头；
- 屏蔽 password、access / refresh token、Authorization、Cookie / Set-Cookie、API key、secret、CSRF、OTP 等常见字段，以及 Bearer / JWT 文本；
- `/api/v1/auth/**` 永不采集请求或响应，环境变量中的 `RADAR_INCLUDE_PATHS` 也不能覆盖此规则；
- SQL 结构仍可用于诊断，但字符串字面量与注释会脱敏；绑定参数值不落库，只保留参数数量或批量行数；
- 异常堆栈不包含局部变量；请求列表不返回 headers、body 或 traceback，详情接口只返回脱敏后的内容；
- 普通业务字段 `code` / `msg` 不自动隐藏，以保证筛选和仪表盘统计正常。不要把验证码或其他秘密放在通用 `code` / `msg` 字段中。

读取旧记录时会再次脱敏，避免历史明文经 Radar API 返回；这不会改写数据库里已经存在的原始记录。

### 升级后的历史数据处置

本修复不会自动删除 Radar 历史数据或修改数据库结构。若旧版本曾对外运行并开启 Radar：

1. 检查反向代理 / 网关中 `/__radar/api` 的历史访问记录，评估是否有人读取过数据；
2. 先使可能暴露的 token 失效并重置密码、API key 等凭据；若怀疑签名密钥泄露或需要全局失效，再评估 Sqids 影响后轮换 `SECRET_KEY`；
3. 先备份 `DB_URL` 对应数据库，再按事故处置流程决定是否清理 `radar_requests`。其关联的 SQL 与用户日志会级联删除，属于破坏性操作，必须另行取得明确授权。

系统不会自动执行 Radar 保留期清理；`RADAR_RETENTION_HOURS` 只是手工调用 `DELETE /__radar/api/purge` 时的默认保留时长。该接口受 RBAC 保护，调用前仍应确认备份、范围和保留策略。

### radar_log — 业务埋点

```python
from app.utils import radar_log

radar_log("用户登录成功", data={"userName": "admin", "userId": 1})
radar_log("权限拒绝", level="ERROR", data={"method": "POST", "path": "/x"})
radar_log("仅 radar，不落文件日志", log_to_file=False)
```

参数：

| 参数 | 默认 | 说明 |
|---|---|---|
| `message` | — | 日志正文 |
| `level` | `"INFO"` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `data` | `None` | dict，自动 json 序列化 |
| `log_to_file` | `True` | 同时输出到 loguru 文件日志 |

只有请求已进入 Radar 采集上下文时才会追加 `radar_user_logs`；若请求未采集且 `log_to_file=False`，这条日志不会持久化。

效果：

- Loguru 文件日志：`<time> | INFO | 用户登录成功 | {"userName": "admin", "userId": 1}`
- Radar Dashboard：在该请求的"用户日志"时间线里附加一条，含调用方 `module.func:line`

### 推荐用法

| 场景 | 推荐 |
|---|---|
| 关键业务节点（登录、状态变更、支付） | `radar_log` + `data` |
| 权限拒绝 / 异常分支 | `radar_log(level="ERROR", data=...)` |
| 高频度调试日志 | 用 `log.debug(...)` 不上 radar |
| 请求 / SQL 自动捕获，不需要手写 | radar 已经做了，别重复 |

## [fastapi-guard](https://fastapi-guard.com/)

第三方请求级别的限流 + 自动封禁。

```bash
# .env
GUARD_ENABLED=true             # 默认 true
GUARD_RATE_LIMIT=100           # 每窗口内允许的请求数
GUARD_RATE_LIMIT_WINDOW=60     # 窗口大小（秒）
GUARD_AUTO_BAN_THRESHOLD=10    # 触发封禁的违规次数
GUARD_AUTO_BAN_DURATION=21600  # 封禁时长（秒，6 小时）
```

触发后返回：

| 码 | 说明 |
|---|---|
| `2500 RATE_LIMITED` | 请求过于频繁 |
| `2501 IP_BANNED` | IP 已被自动封禁 |
| `2502 ACCESS_DENIED` | 被安全策略拦截 |

### 反代场景

启用 `PROXY_HEADERS_ENABLED=true` 后 `granian` 会从 `X-Forwarded-For` / `X-Forwarded-Proto` 还原真实客户端 IP，guard 才能正确识别。**生产环境部署在 Nginx 之后务必启用**，否则所有请求都会被识别为 nginx 容器的 IP，触发误封。

```bash
PROXY_HEADERS_ENABLED=true
TRUSTED_HOSTS=["127.0.0.1", "10.0.0.0/8"]  # 信任的上游
```

### 排查"被封了怎么办"

```bash
# 直接清掉 guard 的 Redis 计数 / 封禁名单
redis-cli --scan --pattern "fastapi_guard:*" | xargs redis-cli del
```

或者 .env 里临时把 `GUARD_ENABLED=false` 重启。

## 日志（Loguru）

- 配置在 [`app/core/log.py`](../../../app/core/log.py)
- 日志输出位置：`logs/`（由 `APP_SETTINGS.LOGS_ROOT` 指定）
- 普通日志保留时间：`LOG_INFO_RETENTION="30 days"`（支持 `seconds/minutes/hours/days/weeks/months/years`）

业务里直接：

```python
from app.utils import log

log.info("..."); log.warning("..."); log.error("..."); log.exception("...")
```

`radar_log` 内部会同时调用 loguru，所以**不需要重复**写两次。

## guard_core 日志噪音抑制

[fastapi-guard](https://fastapi-guard.com/) 的内部库 `guard_core` 会自己加 StreamHandler 并输出冗长 INFO，[`create_app`](../../../app/__init__.py) 启动时会清掉它的 handler 并把级别提到 WARNING，不影响业务日志。

## 相关

- [认证 / radar_log 用法](../develop/auth.md#操作审计--radar_log)
- [配置](./config.md) — RADAR / GUARD / PROXY 相关 env 全集
