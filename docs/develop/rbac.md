# RBAC（菜单 / API / 按钮）

经典 RBAC：用户 ↔ 角色 ↔ {菜单 / API / 按钮}；超级管理员 `R_SUPER` 跳过所有校验。本文聚焦数据模型与运行时；**JWT / 失效**见 [认证](./auth.md)，**行级范围**见 [数据权限](./data-scope.md)。

## 关系图

```
User
`-- M2M --> Role
    |-- M2M --> Menu        前端可见的路由
    |-- M2M --> Button      页面内可执行的按钮
    |-- M2M --> Api         后端可调用的接口
    |-- FK  --> Menu        角色登录后默认首页
    `-- field: data_scope
```

源模型：[`app/system/models/admin.py`](../../../app/system/models/admin.py)。

## 三种权限的边界

| 维度 | 控制 | 由谁声明 | 何时校验 |
|---|---|---|---|
| **菜单** | 前端可见的路由树 | `init_data.py` 的 `ensure_menu` | `GET /api/v1/route/user-routes` 时按角色过滤 |
| **API** | 后端接口可调用 | `refresh_api_list` 自动从 FastAPI 路由对账 | `DependPermission` 在请求阶段校验 |
| **按钮** | 页面内具体操作 | `init_data.py` 的 `ensure_menu(buttons=...)` | `require_buttons` 装饰器；前端 `hasAuth(...)` |

> 同一操作通常需要"按钮 + API"双层授权。前端只藏按钮不安全，后端只挡 API 体验差。

## 超级管理员

- 角色编码 `R_SUPER`（[`app.core.constants.SUPER_ADMIN_ROLE`](../../../app/core/constants.py)）
- `DependPermission` / `require_buttons` / `require_roles` 都会先检查 `R_SUPER` 并直接放行
- `_ensure_super_role()` 在每次启动时把全部非常量菜单 + 全部按钮关联回该角色，免去手动维护

## 角色状态与缓存

只有 `status_type=enable` 的角色参与菜单、API、按钮、数据范围和 `R_SUPER` 判断。关闭角色后会清除该角色权限缓存，并刷新所有关联用户的角色与首页缓存；用户没有其他启用角色时，权限接口返回 `2207 USER_NO_ROLE`。角色重新启用或修改角色编码时同样刷新关联缓存，旧角色编码的缓存键会被删除。

## 菜单与按钮：声明式

每个模块在自己的 `init_data.py` 中声明菜单（含按钮），由 `ensure_menu` upsert 到 `Menu` / `Button` 表：

```python
INVENTORY_MENU_CHILDREN = [
    {
        "menu_name": "商品管理",
        "route_name": "inventory_product",
        "route_path": "/inventory/product",
        "buttons": [
            {"button_code": "B_INVENTORY_PRODUCT_CREATE", "button_desc": "创建商品"},
            {"button_code": "B_INVENTORY_PRODUCT_EDIT",   "button_desc": "编辑商品"},
            {"button_code": "B_INVENTORY_PRODUCT_DELETE", "button_desc": "删除商品"},
            {"button_code": "B_INVENTORY_PRODUCT_TRANSITION", "button_desc": "状态流转"},
        ],
    },
]

await ensure_menu(menu_name="库存管理", route_name="inventory", ..., children=INVENTORY_MENU_CHILDREN)
```

需要"删除已声明集合外的子菜单 / 按钮"时启用 `reconcile_menu_subtree(root_route="inventory", ...)`，子树进入 IaC 模式。详见 [启动初始化与对账](./init-data.md)。

## 按钮命名约定

```
B_<MODULE>_<RESOURCE>_<ACTION>
```

| 例 | 含义 |
|---|---|
| `B_INVENTORY_WAREHOUSE_CREATE` | 库存 / 仓库 / 创建 |
| `B_INVENTORY_PRODUCT_TRANSITION` | 库存 / 商品 / 状态流转 |
| `B_INV_PRODUCT_DELETE` | 库存 / 产品 / 删除 |

通用约定：

- 一个按钮对应一类操作，**单删与批量删共用同一个码**（库存模块如此）
- "读列表"不发按钮——靠菜单可见 + API 授权控制即可
- 跨模块复用的按钮（罕见）放在系统层声明

## API：自动对账

`refresh_api_list()`（[源码](../../../app/system/api/utils.py)）在每次启动时：

1. 列出 FastAPI 当前所有 `APIRoute` 的 `(method, path)`
2. 与 `Api` 表里 `is_system=True` 的记录做 set 差集
3. 多余的 → DELETE + Radar warning（"API 已删除"）
4. 缺失的 → INSERT
5. 已存在的 → UPDATE summary / tags

意味着开发者**永远不需要手动维护 Api 表**——加路由、删路由、改 summary 都自动同步。

`Api` 表的 `status_type=disable` 是管理员能在 Web UI 把某条接口"临时停用"的开关，命中时返回 `2200 API_DISABLED`。

### 匹配语义：按 `path_format` 精确命中

`api_path` 字段存的是 FastAPI 的 `APIRoute.path_format`（例如 `/api/v1/business/inventory/products/{id}`，不是某次请求的真实 URL）。`DependPermission` 在请求阶段也用 `request.scope["route"].path_format` 作为键去 Redis 集合里**精确**查表——和入库键同一字符串空间，O(1) 命中。

这意味着 `/resources/{id}` 和 `/resources/sync` 是**两条完全独立**的权限记录，互不覆盖：

- 只给角色授了 `/resources/{id}`，请求 `/resources/sync` → `2201 PERMISSION_DENIED`
- 只给角色授了 `/resources/sync`，请求 `/resources/{id}` → `2201`

::: warning 前提：FastAPI 要先正确匹配到路由
权限键是"路由匹配的产物"，不是请求 URL 的正则。所以**路由注册顺序**必须让静态段优先于参数段（否则 `/sync` 会被 `/{id}` 吃掉，后续权限查的也是 `/{id}` 那条，两边都错）。

- 用 [`CRUDRouter`](./crud-router.md)：内部 `_OrderedRouter` 自动把静态路径排前面，无需关心顺序
- 手写 `APIRouter` 时，把 `@router.post("/sync")` 写在 `@router.get("/{id}")` **前面**
:::

## 角色种子声明

```python
from app.core.data_scope import DataScopeType
from app.system.services import ensure_role

await ensure_role(
    role_name="库存管理员",
    role_code="R_INVENTORY_ADMIN",
    role_desc="库存专员",
    home_route="inventory_product",
    data_scope=DataScopeType.all,
    menus=["home", "inventory", "inventory_warehouse", "inventory_product", "inventory_tag"],
    buttons=["B_INVENTORY_WAREHOUSE_CREATE", "B_INVENTORY_WAREHOUSE_EDIT", ...],
    apis=[
        ("post", "/api/v1/business/inventory/products/search"),
        ("post", "/api/v1/business/inventory/products"),
        ...
    ],
)
```

`ensure_role` 对 `menus / buttons / apis` 三个集合做 **clear-and-readd**（None=不修改，[]=清空，[...]=替换）。

### 漂移 warning

声明的 `route_name` / `button_code` / `(method, path)` 在 DB 中找不到时输出：

```
ensure_role 'R_INVENTORY_ADMIN': missing apis [('post', '/api/v1/business/inventory/old')] (route signature changed?)
```

**看到必须修**——意味着 seed 与代码脱节。详见 [启动初始化与对账](./init-data.md#ensure_role-配置漂移告警)。

### data_scope 必须显式

`ensure_role(..., data_scope=...)` 不传时**沿用 `Role` 模型默认值 `all`**——这对范围角色 / 普通用户来说是错误的全可见。**业务角色一律显式声明** `data_scope`。详见 [数据权限](./data-scope.md)。

## 后端鉴权依赖

```python
from app.utils import DependPermission, require_buttons, require_roles
```

| 依赖 | 用法 | 失败码 |
|---|---|---|
| `DependPermission` | 路由分组（`include_router(..., dependencies=[DependPermission])`） | `2200 / 2201` |
| `require_buttons("B_X", ...)` | 任一即可 | `2203` |
| `require_buttons(..., require_all=True)` | 必须全部 | `2202` |
| `require_roles("R_X", ...)` | 任一即可 | `2205` |
| `require_roles(..., require_all=True)` | 必须全部 | `2204` |

`R_SUPER` 自动通过。详见 [认证 / 鉴权依赖](./auth.md#鉴权依赖)。

## 前端按钮鉴权

按钮编码通过 `GET /api/v1/auth/user-info` 下发到前端（来源是 `CTX_BUTTON_CODES`；`R_SUPER` 直接返回**全部**按钮码）。前端用 `hasAuth('B_INVENTORY_PRODUCT_CREATE')` 判断是否渲染对应按钮——具体写法见 [前端 / Hooks / useTable / 配合权限按钮](../frontend/hooks/use-table.md#配合权限按钮)。

## 缓存

| Redis Key | 内容 |
|---|---|
| `role:{code}:menus` | 角色菜单 ID 列表 |
| `role:{code}:apis` | `[{method, path, status}]` |
| `role:{code}:buttons` | 按钮编码列表 |
| `role:{code}:data_scope` | 数据范围 |
| `user:{uid}:roles` | 用户角色编码列表 |
| `user:{uid}:role_home` | 用户首页路由名 |

写入时机：

- 启动时 `refresh_all_cache(redis)` 全量加载
- 角色 / 用户 / 菜单 CUD 时业务侧调 `load_role_permissions(redis, role_code=...)` / `load_user_roles(redis, user_id=...)` 增量更新

`DependAuth` / `DependPermission` 都是直接读 Redis；Redis 故障时 fallback 到数据库（带 WARNING 日志）。详见 [缓存](../ops/cache.md)。

## 相关

- [认证（JWT / token_version / impersonate）](./auth.md)
- [数据权限（行级 data_scope）](./data-scope.md)
- [启动初始化与对账](./init-data.md)
- [响应码 22xx 段](../reference/codes.md#22xx--授权)
