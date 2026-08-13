# 响应码

所有接口返回 `{"code": "xxxx", "msg": "...", "data": ...}`，HTTP 状态恒为 200，业务结果由 `code` 字段承载。

源码：[app/core/code.py](../../../app/core/code.py)。前端 `.env` 的 `VITE_SERVICE_*` 把若干码映射为"登出 / 弹窗 / 自动刷新 token / 静默失败"等行为。

## 码段划分

| 码段 | 含义 |
|---|---|
| `0000` | 成功 |
| `1000–1999` | 系统内部错误（异常捕获、入参校验失败） |
| `2000–2999` | 框架内置业务错误（认证、授权、资源冲突、Schema 必填等） |
| `3000–3999` | 框架预留（暂未使用） |
| `4000–9999` | 项目 / 业务模块自定义码（业务模块码必须从 `4000` 起，**不得**占用 `2xxx`） |

## 0000 — 成功

| 码 | 常量 | 说明 |
|---|---|---|
| `0000` | `Code.SUCCESS` | 请求成功 |

## 1xxx — 系统内部错误

### 10xx — 服务器错误

| 码 | 常量 | 说明 |
|---|---|---|
| `1000` | `INTERNAL_ERROR` | 通用 / 未处理异常 |

### 11xx — 数据库错误

| 码 | 常量 | 说明 |
|---|---|---|
| `1100` | `INTEGRITY_ERROR` | 唯一键 / 外键约束冲突 |
| `1101` | `NOT_FOUND` | 记录不存在（`DoesNotExist`） |

### 12xx — 数据校验

| 码 | 常量 | 说明 |
|---|---|---|
| `1200` | `REQUEST_VALIDATION` | 请求参数 / 请求体校验失败（FastAPI 层） |
| `1201` | `RESPONSE_VALIDATION` | 响应序列化失败 |

> `1200` 的 `data.errors` 数组里每条错误形如 `{field, message, type}`，由 [`exceptions.py`](../../../app/core/exceptions.py) 的 `_format_validation_error` 把 Pydantic v2 的英文错误翻译成中文。

## 2xxx — 业务逻辑错误

### 21xx — 认证（前端有特殊处理）

| 码 | 常量 | 说明 | 前端行为 |
|---|---|---|---|
| `2100` | `INVALID_TOKEN` | Token 缺失 / 解码失败 / 格式无效 | 跳转登录 |
| `2101` | `INVALID_SESSION` | Token 类型错误 / 用户不存在 | 跳转登录 |
| `2102` | `ACCOUNT_DISABLED` | 用户账号已禁用 | 弹窗后登出 |
| `2103` | `TOKEN_EXPIRED` | access token 已过期 | 自动刷新 token |
| `2104` | `REFRESH_TOKEN_MISSING` | 刷新令牌缺失 | — |
| `2105` | `NOT_REFRESH_TOKEN` | 传入的不是刷新令牌 | — |
| `2106` | `SESSION_INVALIDATED` | `token_version` 已递增，旧 token 失效 | 跳转登录 |

> 前端 `.env` 中 `VITE_SERVICE_LOGOUT_CODES=2100,2101,2104,2105`、`VITE_SERVICE_MODAL_LOGOUT_CODES=2102,2106`、`VITE_SERVICE_EXPIRED_TOKEN_CODES=2103`。

### 22xx — 授权

| 码 | 常量 | 说明 |
|---|---|---|
| `2200` | `API_DISABLED` | 接口被管理员禁用 |
| `2201` | `PERMISSION_DENIED` | RBAC 接口权限不足 |
| `2202` | `MISSING_BUTTON_PERMISSION` | `require_buttons(..., require_all=True)` 缺指定按钮 |
| `2203` | `NEED_ANY_BUTTON_PERMISSION` | `require_buttons(...)` 任一按钮都不持有 |
| `2204` | `MISSING_ROLE` | `require_roles(..., require_all=True)` 缺指定角色 |
| `2205` | `NEED_ANY_ROLE` | `require_roles(...)` 任一角色都不持有 |
| `2206` | `SUPER_ADMIN_ONLY` | 仅超级管理员可操作 |
| `2207` | `USER_NO_ROLE` | 用户未绑定任何角色 |

### 23xx — 资源冲突

| 码 | 常量 | 说明 |
|---|---|---|
| `2300` | `DUPLICATE_RESOURCE` | 通用资源重复（兜底） |
| `2301` | `DUPLICATE_ROLE_CODE` | 角色编码已存在 |
| `2302` | `DUPLICATE_USER_EMAIL` | 邮箱已注册 |
| `2303` | `DUPLICATE_USER_PHONE` | 手机号已注册 |
| `2304` | `DUPLICATE_USER_NAME` | 用户名已存在 |
| `2305` | `DUPLICATE_MENU_ROUTE` | 菜单路由路径已存在 |

### 24xx — 通用业务失败

| 码 | 常量 | 说明 |
|---|---|---|
| `2400` | `FAIL` | 未归类失败（**尽量避免使用**，新增场景请加专属码） |
| `2401` | `WRONG_CREDENTIALS` | 用户名或密码错误 |
| `2402` | `CAPTCHA_INVALID` | 验证码错误或已过期 |
| `2403` | `CAPTCHA_SEND_FAILED` | 验证码发送失败 |
| `2404` | `PHONE_NOT_REGISTERED` | 手机号未注册 |
| `2405` | `OLD_PASSWORD_WRONG` | 修改密码时原密码错误 |
| `2406` | `TARGET_USER_NOT_FOUND` | 操作目标用户不存在（如模拟登录） |
| `2407` | `STATE_TRANSITION_INVALID` | 不允许的状态流转 |

### 25xx — 限流 / 安全

| 码 | 常量 | 说明 |
|---|---|---|
| `2500` | `RATE_LIMITED` | 请求过于频繁 |
| `2501` | `IP_BANNED` | IP 已被临时封禁 |
| `2502` | `ACCESS_DENIED` | 被安全策略拦截 |

### 26xx — Schema 必填校验（业务 Schema 层主动抛）

| 码 | 常量 | 说明 |
|---|---|---|
| `2600` | `PARAM_REQUIRED` | 通用必填兜底 |
| `2601` | `USERNAME_REQUIRED` | 用户名不能为空 |
| `2602` | `PASSWORD_REQUIRED` | 密码不能为空 |
| `2603` | `USER_ROLE_REQUIRED` | 用户至少需要一个角色 |
| `2604` | `USER_EMAIL_REQUIRED` | 用户邮箱不能为空 |
| `2605` | `ROLE_NAME_REQUIRED` | 角色名称不能为空 |
| `2606` | `ROLE_CODE_REQUIRED` | 角色编码不能为空 |
| `2607` | `ROUTE_NAME_REQUIRED` | 路由名称不能为空 |
| `2608` | `ROUTE_PATH_REQUIRED` | 路由路径不能为空 |

## 4000–9999 — 自定义

项目专属业务码段。框架本身不使用，前端默认不会自动弹错——按需自行处理。

> 业务模块约定：业务码统一从 `4000` 起（不得占用 `2xxx` 系统段），在 `app/core/code.py` 末尾追加本模块的码段（如 `41xx`、`42xx`），**不要**反复使用 `2400`。每个失败场景一个唯一码，便于前端精确弹窗与测试断言。

`main` 不预置任何具体业务模块的 `4xxx` 常量。`example` 分支为 HR 示例保留以下专属码：

| 码 | 常量 | 说明 |
|---|---|---|
| `4000` | `HR_DEPARTMENT_REQUIRED` | 创建员工需要指定有效部门 |
| `4001` | `HR_MANAGER_REQUIRED` | 仅部门主管可执行该操作 |
| `4002` | `HR_CREATE_FORBIDDEN` | 无权限创建员工 |
| `4003` | `HR_TAGS_EXCEED_LIMIT` | 员工标签数量超出上限 |
| `4004` | `HR_EMPLOYEE_NOT_IN_DEPT` | 员工不在当前主管部门中 |
| `4005` | `HR_USER_NOT_EMPLOYEE` | 当前用户未关联员工信息 |
| `4006` | `HR_MANAGER_ONLY` | 仅部门主管可执行该操作 |
| `4007` | `HR_INVALID_TRANSITION` | HR 员工状态流转无效 |

HR 状态机通过 `StateMachine(..., error_code=Code.HR_INVALID_TRANSITION)` 显式使用 `4007`；其他业务模块应为自己的失败场景分配唯一码。

## 抛出方式

业务代码统一抛 `BizError`（或返回 `Fail`）。`BizError` 由 [`exceptions.py`](../../../app/core/exceptions.py) 的全局处理器捕获并转成 `Fail(code, msg)`：

```python
from app.utils import BizError, Code, Fail

# 方式 A：抛异常（推荐，能在任意层穿透）
raise BizError(code=Code.STATE_TRANSITION_INVALID, msg="不允许从 'draft' 转换为 'archived'")

# 方式 B：返回 Fail（仅在 api 层用，更直白）
return Fail(code=Code.OLD_PASSWORD_WRONG, msg="原密码错误")
```

`SchemaValidationError`（继承自 `BizError`）专用于 Pydantic 校验器中抛出：它**不**继承 `ValueError`，因此 Pydantic 不会捕获，能直达全局处理器。

## 前端码映射

| 前端 .env 变量 | 默认值 | 行为 |
|---|---|---|
| `VITE_SERVICE_SUCCESS_CODE` | `0000` | 视为成功，提取 `data` |
| `VITE_SERVICE_LOGOUT_CODES` | `2100,2101,2104,2105` | 直接登出 |
| `VITE_SERVICE_MODAL_LOGOUT_CODES` | `2102,2106` | 弹窗提示后登出 |
| `VITE_SERVICE_EXPIRED_TOKEN_CODES` | `2103` | 自动用 refresh token 刷新并重试 |
| 其他 | — | 显示 `msg` 错误消息 |
