# RBAC (menus / APIs / buttons)

Classic RBAC: User ↔ Role ↔ {Menu / Button / API}; `R_SUPER` bypasses every check. This page covers the data model and runtime; **JWT / invalidation** is in [Auth](/en/develop/auth); **row-level scope** is in [Data scope](/en/develop/data-scope).

## Relationships

```
User
`-- M2M --> Role
    |-- M2M --> Menu        frontend-visible routes
    |-- M2M --> Button      in-page actionable buttons
    |-- M2M --> Api         callable backend endpoints
    |-- FK  --> Menu        default landing page
    `-- field: data_scope
```

Source models: `app/system/models/admin.py`.

## Three permission dimensions

| Dimension | Controls | Declared by | Checked when |
|---|---|---|---|
| **Menu** | Frontend-visible route tree | `init_data.py`'s `ensure_menu` | `GET /api/v1/route/user-routes` filters by role |
| **API** | Callable backend endpoint | `refresh_api_list` auto-reconciles from FastAPI routes | `DependPermission` per request |
| **Button** | In-page action | `init_data.py`'s `ensure_menu(buttons=...)` | `require_buttons` (backend); `hasAuth(...)` (frontend) |

> An action typically needs both "button + API". Hiding only the button isn't safe; only blocking the API hurts UX.

## Super admin

- Code `R_SUPER` (`app.core.constants.SUPER_ADMIN_ROLE`)
- `DependPermission` / `require_buttons` / `require_roles` short-circuit on `R_SUPER`
- `_ensure_super_role()` re-attaches every non-constant menu + every button to this role on every startup

## Role status and cache refresh

Only roles with `status_type=enable` participate in menus, APIs, buttons, data scopes, or the `R_SUPER` check. Disabling a role clears its permission cache and refreshes every associated user's role and home-route cache; a user with no other enabled role receives `2207 USER_NO_ROLE`. Re-enabling or renaming a role also refreshes associated caches and deletes keys for the old role code.

## Menus and buttons: declarative

Each module declares menus (with their buttons) in its `init_data.py`; `ensure_menu` upserts into `Menu` / `Button`:

```python
INVENTORY_MENU_CHILDREN = [
    {
        "menu_name": "Products",
        "route_name": "inventory_product",
        "route_path": "/inventory/product",
        "buttons": [
            {"button_code": "B_INVENTORY_PRODUCT_CREATE", "button_desc": "create product"},
            {"button_code": "B_INVENTORY_PRODUCT_EDIT",   "button_desc": "edit product"},
            {"button_code": "B_INVENTORY_PRODUCT_DELETE", "button_desc": "delete product"},
            {"button_code": "B_INVENTORY_PRODUCT_TRANSITION", "button_desc": "state transition"},
        ],
    },
]

await ensure_menu(menu_name="Inventory", route_name="inventory", ..., children=INVENTORY_MENU_CHILDREN)
```

To "delete entries that are no longer in the seed", enable `reconcile_menu_subtree(root_route="inventory", ...)` — the subtree enters IaC mode. See [Init data](/en/develop/init-data).

## Button naming convention

```
B_<MODULE>_<RESOURCE>_<ACTION>
```

| Example | Meaning |
|---|---|
| `B_INVENTORY_WAREHOUSE_CREATE` | Inventory / warehouse / create |
| `B_INVENTORY_PRODUCT_TRANSITION` | Inventory / product / state transition |
| `B_INV_PRODUCT_DELETE` | Inventory / product / delete |

General rules:

- One button = one action category; **single delete + batch delete share one code** (Inventory does this)
- "Read list" doesn't need a button — menu visibility + API authorization are enough
- Truly cross-module buttons (rare) live in the system layer

## API: auto-reconciled

`refresh_api_list()` (`app/system/api/utils.py`) on every startup:

1. Lists all `APIRoute`s' `(method, path)`
2. Set-diffs against `Api` rows where `is_system=True`
3. Extras → DELETE + Radar warning ("API deleted")
4. Missing → INSERT
5. Existing → UPDATE summary / tags

Developers **never** maintain the `Api` table by hand — adding / removing / renaming routes auto-syncs.

`Api.status_type=disable` lets an admin temporarily disable an endpoint via Web UI; hits return `2200 API_DISABLED`.

## Role seed declaration

```python
from app.core.data_scope import DataScopeType
from app.system.services import ensure_role

await ensure_role(
    role_name="inventory admin",
    role_code="R_INVENTORY_ADMIN",
    role_desc="Inventory specialist",
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

`ensure_role` does **clear-and-readd** for `menus / buttons / apis` (None=skip, []=clear, [...] = replace).

### Drift warnings

When a declared `route_name` / `button_code` / `(method, path)` doesn't exist in the DB:

```
ensure_role 'R_INVENTORY_ADMIN': missing apis [('post', '/api/v1/business/inventory/old')] (route signature changed?)
```

**Fix on sight** — the seed is out of sync with the code. See [Init data / drift](/en/develop/init-data).

### data_scope must be explicit

Omitting `data_scope` on `ensure_role(...)` keeps the model default `all` — wrong for scoped roles / regular users. **Always set it explicitly** in business role seeds. See [Data scope](/en/develop/data-scope).

## Backend dependencies

```python
from app.utils import DependPermission, require_buttons, require_roles
```

| Dependency | Use | Failure code |
|---|---|---|
| `DependPermission` | Mount on a router group (`include_router(..., dependencies=[DependPermission])`) | `2200 / 2201` |
| `require_buttons("B_X", ...)` | any one | `2203` |
| `require_buttons(..., require_all=True)` | all required | `2202` |
| `require_roles("R_X", ...)` | any one | `2205` |
| `require_roles(..., require_all=True)` | all required | `2204` |

`R_SUPER` always passes. See [Auth / dependencies](/en/develop/auth#auth-dependencies).

## Frontend button gating

Button codes are delivered via `GET /api/v1/auth/user-info` (sourced from `CTX_BUTTON_CODES`; `R_SUPER` users get **all** codes). The frontend uses `hasAuth('B_INVENTORY_PRODUCT_CREATE')` to decide whether to render a button — see [Frontend / Hooks / useTable / Pair with permission buttons](/en/frontend/hooks/use-table#pair-with-permission-buttons).

## Cache

| Redis Key | Content |
|---|---|
| `role:{code}:menus` | menu IDs |
| `role:{code}:apis` | `[{method, path, status}]` |
| `role:{code}:buttons` | button codes |
| `role:{code}:data_scope` | data scope |
| `user:{uid}:roles` | role codes |
| `user:{uid}:role_home` | route name of home page |

Write timing:

- Startup `refresh_all_cache(redis)` loads everything
- After role / user / menu CUD, the business calls `load_role_permissions(redis, role_code=...)` / `load_user_roles(redis, user_id=...)` to update incrementally

`DependAuth` / `DependPermission` read directly from Redis; on Redis failure they fall back to DB (with WARNING). See [Cache](/en/ops/cache).

## See also

- [Auth (JWT / token_version / impersonate)](/en/develop/auth)
- [Data scope](/en/develop/data-scope)
- [Init data](/en/develop/init-data)
- [Response codes 22xx](/en/reference/codes#22xx--authorization)
