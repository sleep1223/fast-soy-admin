# 认证

JWT + Argon2 密码哈希 + Redis 协助的会话失效机制。RBAC 与数据权限独立成文：

- [RBAC（菜单 / API / 按钮）](./rbac.md)
- [数据权限（data_scope）](./data-scope.md)

源码：[app/system/security.py](../../../app/system/security.py)、[app/system/services/auth.py](../../../app/system/services/auth.py)、[app/core/dependency.py](../../../app/core/dependency.py)。

## JWT 配置

| 项 | 默认 | 设置位置 |
|---|---|---|
| 算法 | HS256 | `JWT_ALGORITHM` |
| Access Token | 12 小时 | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`（分钟） |
| Refresh Token | 7 天 | `JWT_REFRESH_TOKEN_EXPIRE_MINUTES`（分钟） |
| 签名密钥 | 内置开发用 | `SECRET_KEY`（**生产必须改**） |
| 密码哈希 | Argon2 | [`app/system/security.py`](../../../app/system/security.py) |

> `SECRET_KEY` 还会被 [`app/core/sqids.py`](../../../app/core/sqids.py) 用作字母表派生的种子。**轮换 SECRET_KEY 会同时使所有 JWT 与历史 sqid 失效**，请配套规划数据迁移。

## Token 结构

```json
{
  "iat": 1712...,
  "exp": 1712...,
  "data": {
    "userId": 123,
    "userName": "Soybean",
    "tokenType": "accessToken",   // accessToken | refreshToken
    "tokenVersion": 0,            // 与 Redis token_version:{userId} 对比
    "impersonatorId": 0           // 模拟登录时为操作人 ID
  }
}
```

## 登录流程

```
POST /api/v1/auth/login  { userName, password }
   │
   ▼
login_with_credentials()
   ├─ User.filter(user_name=...).first()
   ├─ verify_password(plain, hash)       # Argon2
   ├─ 检查 status_type == enable
   ├─ update_last_login()
   ├─ token_version = redis.get("token_version:{uid}") ?? 0
   └─ build_tokens(user, token_version)  # access + refresh
   │
   ▼
返回 { token, refreshToken, mustChangePassword }
```

### 验证码登录 / 注册

`POST /captcha` → 后端发送（`send_captcha`），Redis 暂存 5 分钟。
`POST /code-login` 与 `POST /register` 都先 `verify_captcha(redis, phone, code)`。

### 模拟登录

```
POST /api/v1/auth/impersonate/{userId}
  ├─ 仅 R_SUPER 可调用（否则 2206 SUPER_ADMIN_ONLY）
  └─ build_tokens(target_user, ..., impersonator_id=current_user_id)
```

签发的 token 携带 `impersonatorId`，`/user-info` 接口会回返 `{"impersonating": true, "impersonatorId": ...}`，前端据此显示"正在以 XXX 身份操作"提示并提供"退出模拟"入口。

## Token 刷新

```
POST /api/v1/auth/refresh-token  { refreshToken }
   │
   ├─ check_token(refreshToken)  # 签名 + exp
   ├─ data["tokenType"] == "refreshToken"   else 2105
   ├─ user.status_type == enable             else 2102
   ├─ tokenVersion ≥ redis.token_version    else 2106
   └─ 重新签发 access + refresh
```

`access` 过期触发码 `2103`，前端拦截后**自动**用 `refreshToken` 调本接口、更新本地 token，再重放原始请求。

## Token 失效（token_version）

修改密码、关闭用户、模拟登录恢复、管理员强制下线等场景需要"立即让旧 token 失效"。机制：

- 每个用户在 Redis 有键 `token_version:{userId}`，初始 `0`
- 签发新 token 时把当前版本号写入 JWT payload
- 每次请求时 `AuthControl.is_authed` 把 JWT 中的版本号与 Redis 中的最新版本号比较，更小则抛 `2106 SESSION_INVALIDATED`
- 触发失效时调 `invalidate_user_session(redis, user_id)`：`INCR token_version:{user_id}`，旧 token 立刻失效

关闭用户时，请求优先返回 `2102 ACCOUNT_DISABLED`；重新启用后，关闭前签发的旧 token 再返回 `2106 SESSION_INVALIDATED`，不会恢复有效。

```python
# 修改密码后失效
@router.patch("/password", dependencies=[DependAuth])
async def _(body: UpdatePassword, request: Request):
    ...
    await User.filter(id=user_id).update(password=...)
    await invalidate_user_session(request.app.state.redis, user_id)
    return Success(msg="密码修改成功，请重新登录")
```

> Redis 不可用时会 fallback 到"放行 + WARNING 日志"，避免缓存故障导致全员被踢出。

## 必须改密码

`User.must_change_password=True` 的账号登录后，`/login` 响应里 `mustChangePassword=true`，前端引导跳转修改密码页。`PATCH /password` 成功后自动置 `False`。

种子用户场景：用 `ensure_user(..., must_change_password=True)` 初始化（库存模块创建商品时也会用此模式 + 随机初始密码）。

## 鉴权依赖

### `DependAuth` — 仅认证

```python
from app.utils import DependAuth

@router.get("/me", dependencies=[DependAuth])
async def me():
    user_id = get_current_user_id()
    ...
```

执行步骤（[`AuthControl.is_authed`](../../../app/core/dependency.py)）：

1. 从 `Authorization: Bearer xxx` 提取 token，缺失 → `2100`
2. `jwt.decode` 验签 + 检查 exp（过期 → `2103`，无效 → `2100`）
3. 校验 `tokenType == "accessToken"`，否则 `2101`
4. 加载 `User`，非启用或不存在 → `2102 / 2101`
5. Redis 比较 `tokenVersion`，旧版 → `2106`
6. 加载角色 / 按钮 → 写入 `CTX_USER_ID / CTX_USER / CTX_ROLE_CODES / CTX_BUTTON_CODES`
7. Redis 失败时 fallback 到数据库查询，并且只加载启用角色（WARNING 日志）

### `DependPermission` — 接口权限

```python
@router.get("/users/{id}", dependencies=[DependPermission])
```

在 `DependAuth` 之上：

1. `R_SUPER` 角色直接放行
2. 用户无任何角色 → `2207`
3. 汇总所有角色的 `(method, path, status)` 三元组（`path` 即 `APIRoute.path_format`，与 `refresh_api_list()` 入库保持同一字符串空间）
4. 以 `request.scope["route"].path_format`（FastAPI 匹配完成后回填的路由模板）为键，对 `(method.lower(), path_format)` 做**精确**查表命中
5. 命中且 `status == enable` → 放行；命中但 `disable` → `2200`；未命中 → `2201`；`scope["route"]` 不是 `APIRoute`（理论上不会发生） → `2201`

通常通过 `router.include_router(..., dependencies=[DependPermission])` 在路由分组上挂一次即可。

::: tip 为什么不用正则匹配请求 URL
早期实现把 `api_path` 里的 `{xxx}` 替换为 `[^/]+` 再用 `re.match` 去对 `request.url.path` 做匹配。这会带来两类安全问题：

- **参数路径吃掉静态兄弟**：拥有 `GET /resources/{id}` 权限的用户，请求 `GET /resources/sync` 也会通过——因为 `/resources/[^/]+` 能匹到 `sync`。
- **`re.match` 未锚定尾部**：拥有 `/users` 权限会误命中 `/users-extra`、`/users/delete-all` 等更长的 URL。

现改为直接用 FastAPI 已匹配到的 `APIRoute.path_format` 做 O(1) 集合命中，和 `refresh_api_list()` 入库键完全同构——静态路由和参数路由在字符串层面天然隔离，无法互相蹭权限。

前提是**让 FastAPI 先正确匹配到静态路由**：手写路由时必须把静态段（`/sync`）注册在参数段（`/{id}`）之前，或直接使用 `CRUDRouter`（内部 `_OrderedRouter` 自动把静态路径排到前面）。详见 [CRUDRouter](./crud-router.md)。
:::

### `require_buttons(...)` — 按钮权限

```python
from app.utils import require_buttons

@router.post("/products", dependencies=[require_buttons("B_INVENTORY_PRODUCT_CREATE")])
async def _(): ...

# 任一按钮即可
@router.patch("/x", dependencies=[require_buttons("B_A", "B_B")])

# 必须全部
@router.patch("/y", dependencies=[require_buttons("B_A", "B_B", require_all=True)])
```

行为：

- `R_SUPER` 自动通过
- `require_all=False`（默认）：任一持有即放行，否则 `2203`
- `require_all=True`：缺任一 → `2202`

::: tip 跟 `CRUDRouter` 配合
推荐用 `action_dependencies={"create": [require_buttons(...)]}` 在工厂层批量挂，对 `@override` 替换的路由也生效。详见 [CRUDRouter](./crud-router.md#action_dependencies)。
:::

### `require_roles(...)` — 角色

接口与 `require_buttons` 同构，码段为 `2204 / 2205`。

## 上下文工具

每次请求都有以下 ContextVars 可用（[`app/core/ctx.py`](../../../app/core/ctx.py)）：

| ContextVar | 类型 | 何时可用 |
|---|---|---|
| `CTX_USER_ID` | `int \| None` | `DependAuth` 后 |
| `CTX_USER` | `User \| None` | `DependAuth` 后 |
| `CTX_ROLE_CODES` | `list[str]` | `DependAuth` 后 |
| `CTX_BUTTON_CODES` | `list[str]` | `DependAuth` 后 |
| `CTX_IMPERSONATOR_ID` | `int \| None` | 模拟登录场景 |
| `CTX_X_REQUEST_ID` | `str` | 中间件中始终有值 |
| `CTX_BG_TASKS` | `BackgroundTasks \| None` | `BackgroundTaskMiddleware` 后 |

便捷函数：

```python
from app.utils import (
    get_current_user_id,    # int  (未认证时抛 LookupError)
    get_current_user,       # User | None
    is_super_admin,         # bool
    has_role_code(code),
    has_button_code(code),
)
```

## 操作审计 — radar_log

```python
from app.utils import radar_log

radar_log("用户登录成功", data={"userName": user.user_name, "userId": user.id})
radar_log("权限拒绝", level="ERROR", data={"method": method, "path": path})
```

`radar_log` 在默认 `log_to_file=True` 时把脱敏后的内容写入 Loguru；只有当前请求被 Radar 采集时，才会同时追加到 `radar_user_logs` 并显示在 `/manage/radar/*`。`/api/v1/auth/**` 永不采集，因此认证请求的埋点不会写入 Radar 表；若同时设置 `log_to_file=False`，则不会持久化。详见 [监控（Radar）](../ops/radar.md)。

## 相关

- [RBAC 模型与按钮权限](./rbac.md)
- [数据权限 data_scope](./data-scope.md)
- [响应码](../reference/codes.md) — 21xx / 22xx 全部码
- [启动初始化与对账](./init-data.md) — 角色 / 菜单 / API 怎么落库
