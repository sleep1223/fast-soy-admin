# 后端风格

后端代码的**强制约定清单**，可直接当 PR review checklist。涵盖响应、Schema、API 路径、CRUD、权限、异常、缓存、命名八块。

::: warning 不是软建议
违反任意一条都视为"待修复"。需破例时请在 PR 中给出明确理由并指向架构决策。
:::

## 1. 响应

- ✅ **必须**用 `Success` / `SuccessExtra` / `Fail`（来自 `app.utils`）
- ❌ **不要**返回裸 dict、`JSONResponse(...)`、`{"code": "0000", ...}` 字面量
- ❌ **不要**手工拼 snake_case 响应——`SchemaBase` / `to_dict()` 都自动 camelCase
- ✅ 每个不同的失败场景**用唯一业务码**（在 `app/core/code.py` 末尾追加），少用 `Code.FAIL` 兜底
- ✅ 业务异常用 `raise BizError(code, msg)`（穿透任意层），仅在 api 层用 `return Fail(...)`

```python
# ✅
return Success(data=await user.to_dict())
return SuccessExtra(data={"records": records}, total=total, current=obj_in.current, size=obj_in.size)
raise BizError(code=Code.STATE_TRANSITION_INVALID, msg="不允许的状态流转")

# ❌
return {"code": "0000", "data": {...}}
return JSONResponse({"code": Code.FAIL, "msg": "失败"})
```

## 2. Schema

- ✅ 业务 schema **必须**继承 `SchemaBase`（自动 snake_case ↔ camelCase）
- ✅ 分页搜索 schema **必须**继承 `PageQueryBase`
- ✅ 资源 ID 字段类型用 `SqidId`，FastAPI 路径参数用 `SqidPath`
- ✅ 整型字段按数据库范围用 `Int16 / Int32 / Int64`
- ✅ Update schema 用 `make_optional(XxxCreate, "XxxUpdate")` 派生，避免冗余字段定义
- ❌ Schema 中**不要** `from pydantic import BaseModel as ...`——业务一律 `from app.utils import SchemaBase`
- ✅ Schema 校验器中要返回业务码时用 `SchemaValidationError(code, msg)`，**不要** `ValueError`

## 3. API 路径与方法

- ✅ 列表：`POST /resources/search`，body 继承 `PageQueryBase`
- ✅ 单条：`GET / PATCH / DELETE /resources/{id}`（id 是 sqid）
- ✅ 创建：`POST /resources`
- ✅ 批量删除：`DELETE /resources`，body 用 `CommonIds`
- ✅ 多词路径用 **kebab-case**（`/batch-offline`、`/user-routes`）
- ✅ 资源名一律 **复数**
- ❌ 路径不带尾斜杠
- ❌ 不要用 `GET /resources?xxx=...&yyy=...` 实现复杂搜索——一律走 `POST /search`

完整约定见 [API 约定](../develop/api.md)。

## 4. 路由层（CRUD）

- ✅ 标准 6 路由用 `CRUDRouter` 生成，**禁止**手写
- ✅ 自定义某条路由用 `@crud.override("create")`，**不要**在 router 上重新声明同路径
- ✅ 按钮权限挂在 `action_dependencies` 上，对 `@override` 路由也生效
- ✅ 标准 6 路由之外的端点直接挂在 `crud.router` 上
- ❌ 不要直接操作 `router.routes.append(...)` 绕过 `_OrderedRouter` 排序
- ❌ Controller / Service 中**不要** import `fastapi.Request` / `Response`——HTTP 相关只在 api 层
- ❌ `@crud.override` 内**禁止**出现 `in_transaction` / `request.app.state.redis` / 跨模型写 / 事件 / 审计——必须下沉到 `services/`，api 层只做参数转发与响应封装
- ❌ 当某资源 override 数 ≥ 3，或该资源是聚合根（带状态、带副作用），**应改为**显式 `@router.post(...)` + `services/`，不要硬塞 `CRUDRouter`（CRUDRouter 只服务贫血资源；详见 [CRUDRouter / 适用边界](../develop/crud-router.md#适用边界-别让-crudrouter-上瘾)）

## 5. 分层职责

| 层 | 必须做 | 必须不做 |
|---|---|---|
| `api/` | URL 接线、依赖、`Success`/`Fail` | 业务规则、跨模型、事务 |
| `services/` | 事务、跨模型、缓存、状态机、事件 | 触发 HTTP（Request/Response） |
| `controllers/` | 单模型 CRUD（继承 `CRUDBase`）、`build_search` | 跨模型编排、事务、缓存、事件派发、外部 IO |
| `models/` | 表字段、索引、关系、Mixin | 业务校验逻辑 |
| `schemas/` | DTO 与字段级校验 | 跨资源逻辑 |

## 6. 权限

- ✅ 写接口（POST/PATCH/DELETE）**必须**挂按钮权限（`require_buttons` 或 `action_dependencies`）
- ✅ 业务角色种子**必须**显式声明 `data_scope`（不要依赖模型默认 `all`）
- ✅ 涉及行级权限的列表接口**必须** `@override("list")` 拼 `build_scope_filter`
- ❌ 不要靠"前端隐藏按钮"做安全——后端必须有对应校验
- ❌ 不要在业务里直接判 `role_code == "R_INVENTORY_ADMIN"`——用 `has_role_code` / `has_button_code`

## 7. 模型

- ✅ 模型一律继承 `BaseModel + AuditMixin`（持久化的）
- ✅ 文件头 `# pyright: reportIncompatibleVariableOverride=false`（Tortoise + Pyright 已知误报）
- ✅ 字段加 `description="..."`（CLI 生成 schema 时会用作 i18n 中文名，截断到第一个句号）
- ✅ 类的 docstring 写中文资源名（`"""客户"""`），用作 API summary 前缀
- ✅ `Meta.table` 用 `biz_<module>_<entity>` 前缀（系统模型在 `app/system/models/` 下用语义化表名）
- ✅ **每个 `ForeignKeyField` / `OneToOneField` 上方显式声明 `<name>_id: int`（或 `int | None`）类型注解**——见下方
- ❌ 不要在 `models.py` 写业务逻辑——字段级校验放 schema、跨模型编排 / 事务 / 事件 / 缓存放 service

### 外键访问规范

Tortoise 的 FK 字段在运行时会自动派生一个 `<name>_id` 属性（同步访问、零查询，对应 DB 列）；`<name>` 本身是**异步懒加载**的关系对象。两者**不是一回事**：

```python
# models.py
class Product(BaseModel, AuditMixin):
    # ✅ 显式声明 _id 类型注解，让 pyright / IDE 能看到该属性
    user_id: int | None
    user: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        "app_system.User", null=True, on_delete=fields.SET_NULL, related_name="product",
    )
    team_id: int
    team: fields.ForeignKeyRelation["Team"] = fields.ForeignKeyField(
        "app_system.Team", related_name="products",
    )
```

使用时按需求选择：

| 需求 | 正确写法 | 错误写法 |
|---|---|---|
| 只要 ID（比较、日志、传给另一个模型的 FK 字段） | `emp.team_id` | `(await emp.team).id` — 多一次查询 |
| 要关系对象的字段（`team.name`） | 先 `prefetch_related("team")` 再读 `emp.team.name` | `emp.team.name` — 懒加载，循环中触发 N+1 |
| 单对象场景、无批量 | `team = await emp.team` | — |
| M2M / 反向关系 | `prefetch_related("by_role_menus")` 后遍历；或显式 `.all()` | 直接 `for m in role.by_role_menus` — `RelatedManager` 不是可迭代对象 |

::: danger 创建 / 更新时不要把未 prefetch 的关系对象当值传
```python
# ❌ 如果 other.team 没有 prefetch，这一行会触发查询；
#    更糟的是 Tortoise 老版本会把 coroutine 对象赋值给 FK，写入时抛 TypeError
new_emp = await Product.create(team=other.team)

# ✅ 总是传 _id
new_emp = await Product.create(team_id=other.team_id)
```

这就是为什么 `_id: int` 注解是强制的——把"用 ID 安全路径"放到开发者眼前，IDE 自动补全也会优先提示。
:::

## 8. 业务模块边界

- ✅ 业务模块 import 入口统一走 `app.utils`
- ✅ 跨业务模块联动用 [事件总线](../develop/events.md)（`emit` / `on`）
- ❌ 业务模块**不得反向 import** `app.system.*`（除了 `ensure_menu` / `ensure_role` 等 system 主动暴露的 service）
- ❌ 业务模块**不得**互相 import（`app.business.crm.*` 不能 `from app.business.inventory import ...`）

## 9. 命名

- 文件 / 目录：`snake_case`
- 类：`PascalCase`
- 函数 / 方法：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- API 路径：`kebab-case`
- Schema 字段（Python 内部）：`snake_case`；HTTP 边界（前端可见）：`camelCase`
- 角色编码：`R_<UPPER>` / 按钮编码：`B_<MODULE>_<RESOURCE>_<ACTION>` / 路由名：`module_subpage`

详见 [命名规范](./naming.md)。

## 10. 类型注解 / 格式化 / 静态检查

- ✅ 所有函数都加类型注解
- ✅ 提交前跑：

```bash
just fmt backend        # ruff check --fix + format
just typecheck backend  # basedpyright
just test backend       # pytest
just check backend      # 上面三条一次跑完
```

- ✅ 行宽 200，双引号，自动排序 import
- ✅ basedpyright standard 模式必须通过

## 11. 异常处理

- ✅ 用 `BizError` / `SchemaValidationError` 抛业务错
- ❌ 不要 `raise HTTPException`（旧别名仅为兼容存在，新代码用 `BizError`）
- ❌ 不要 catch `Exception` 后吞掉——全局处理器会记录日志
- ✅ Service 里需要事务 + 失败补偿用 `in_transaction(get_db_conn(Model))`
- ❌ 不要硬编码连接名（`"conn_system"`），用 `get_db_conn(Model)`

## 12. 缓存

- ✅ 业务自有的小热点（统计 / 选项）按"读 → miss → 查 → 写带 TTL"模式手写
- ✅ 数据变更时**主动失效**对应 key（业务模块的 `cache_utils.py`）
- ❌ 不要给带分页 / 多参数的接口加全局 `@cache(...)` 装饰器
- ✅ 业务 key 命名：`<module>_<resource>:<scope>`（如 `dict_options:tag_category`）

详见 [缓存](../ops/cache.md)。

## 13. 日志与监控

- ✅ 关键业务节点 / 权限拒绝 / 异常分支用 `radar_log`
- ✅ 高频度调试日志直接 `log.debug(...)`，不要全部上 radar
- ❌ 不要 `print(...)`

## 14. 提交前必跑

```bash
just check  # 后端 + 前端所有质量检查
```

包括：`ruff fix + format`、`basedpyright`、`pytest`、`eslint + oxlint`、`vue-tsc`。

## 相关

- [架构](../getting-started/architecture.md) — 总览
- [开发指南](../getting-started/workflow.md) — 用 CLI 创建模块的端到端流程
- [API 约定](../develop/api.md) / [响应码](../reference/codes.md)
- [业务开发](../develop/intro.md)
