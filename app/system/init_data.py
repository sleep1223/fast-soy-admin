from copy import deepcopy

from app.core.config import APP_SETTINGS
from app.core.constants import SUPER_ADMIN_ROLE
from app.core.data_scope import DataScopeType
from app.system.models import Button, Menu, Role, StatusType
from app.system.services import apply_init_data
from app.system.services.init_helper import _safe_update_or_create


def _crud_apis(resource: str, *, with_tree: bool = False) -> list[tuple[str, str]]:
    """生成一组 CRUDRouter 标准路由的 (method, path)（不含 GET 详情，前端均无调用）。"""
    base = f"/api/v1/system-manage/{resource}"
    apis = [
        ("post", f"{base}/search"),
        ("post", base),
        ("patch", f"{base}/{{item_id}}"),
        ("delete", f"{base}/{{item_id}}"),
        ("delete", base),
    ]
    if with_tree:
        apis.append(("get", f"{base}/tree"))
    return apis


RADAR_API_REFS: list[tuple[str, str]] = [
    ("get", "/__radar/api/requests"),
    ("get", "/__radar/api/requests/{x_request_id}"),
    ("get", "/__radar/api/queries"),
    ("get", "/__radar/api/exceptions"),
    ("put", "/__radar/api/exceptions/{x_request_id}/resolve"),
    ("get", "/__radar/api/stats"),
    ("get", "/__radar/api/dashboard"),
    ("delete", "/__radar/api/purge"),
    ("get", "/__radar/api/monitor/overview"),
    ("get", "/__radar/api/monitor/realtime"),
]

SYSTEM_INIT_DATA = {
    "menus": [
        {
            "menu_name": "login",
            "route_name": "login",
            "route_path": "/login",
            "component": "layout.blank$view.login",
            "order": 1,
            "menu_type": "1",
            "constant": True,
            "hide_in_menu": True,
            "props": True,
        },
        {
            "menu_name": "403",
            "route_name": "403",
            "route_path": "/403",
            "component": "layout.blank$view.403",
            "order": 2,
            "menu_type": "1",
            "constant": True,
            "hide_in_menu": True,
        },
        {
            "menu_name": "404",
            "route_name": "404",
            "route_path": "/404",
            "component": "layout.blank$view.404",
            "order": 3,
            "menu_type": "1",
            "constant": True,
            "hide_in_menu": True,
        },
        {
            "menu_name": "500",
            "route_name": "500",
            "route_path": "/500",
            "component": "layout.blank$view.500",
            "order": 4,
            "menu_type": "1",
            "constant": True,
            "hide_in_menu": True,
        },
        {
            "menu_name": "首页",
            "route_name": "home",
            "route_path": "/home",
            "component": "layout.base$view.home",
            "order": 1,
            "icon": "mdi:monitor-dashboard",
        },
        {
            "menu_name": "个人中心",
            "route_name": "user-center",
            "route_path": "/user-center",
            "component": "layout.base$view.user-center",
            "order": 99,
            "i18n_key": "route.user-center",
            "hide_in_menu": True,
        },
        {
            "menu_name": "系统管理",
            "route_name": "manage",
            "route_path": "/manage",
            "order": 1,
            "icon": "carbon:cloud-service-management",
            "children": [
                {
                    "menu_name": "API管理",
                    "route_name": "manage_api",
                    "route_path": "/manage/api",
                    "component": "view.manage_api",
                    "order": 1,
                    "icon": "ant-design:api-outlined",
                },
                {
                    "menu_name": "用户管理",
                    "route_name": "manage_user",
                    "route_path": "/manage/user",
                    "component": "view.manage_user",
                    "order": 2,
                    "icon": "ic:round-manage-accounts",
                },
                {
                    "menu_name": "角色管理",
                    "route_name": "manage_role",
                    "route_path": "/manage/role",
                    "component": "view.manage_role",
                    "order": 3,
                    "icon": "carbon:user-role",
                },
                {
                    "menu_name": "菜单管理",
                    "route_name": "manage_menu",
                    "route_path": "/manage/menu",
                    "component": "view.manage_menu",
                    "order": 4,
                    "icon": "material-symbols:route",
                },
                {
                    "menu_name": "代码生成",
                    "route_name": "manage_codegen",
                    "route_path": "/manage/codegen",
                    "component": "view.manage_codegen",
                    "order": 5,
                    "icon": "mdi:code-json",
                },
                {
                    "menu_name": "用户详情",
                    "route_name": "manage_user-detail",
                    "route_path": "/manage/user-detail/:id",
                    "component": "view.manage_user-detail",
                    "order": 5,
                    "hide_in_menu": True,
                },
                {
                    "menu_name": "性能监控",
                    "route_name": "manage_radar",
                    "route_path": "/manage/radar",
                    "order": 7,
                    "icon": "mdi:radar",
                    "menu_type": "1",
                    "status_type": StatusType.disable,
                    "children": [
                        {
                            "menu_name": "仪表板",
                            "route_name": "manage_radar_overview",
                            "route_path": "/manage/radar/overview",
                            "component": "view.manage_radar_overview",
                            "order": 1,
                            "icon": "mdi:chart-box-outline",
                            "status_type": StatusType.disable,
                        },
                        {
                            "menu_name": "请求列表",
                            "route_name": "manage_radar_requests",
                            "route_path": "/manage/radar/requests",
                            "component": "view.manage_radar_requests",
                            "order": 2,
                            "icon": "mdi:swap-horizontal",
                            "status_type": StatusType.disable,
                        },
                        {
                            "menu_name": "SQL查询",
                            "route_name": "manage_radar_queries",
                            "route_path": "/manage/radar/queries",
                            "component": "view.manage_radar_queries",
                            "order": 3,
                            "icon": "mdi:database-search",
                            "status_type": StatusType.disable,
                        },
                        {
                            "menu_name": "异常列表",
                            "route_name": "manage_radar_exceptions",
                            "route_path": "/manage/radar/exceptions",
                            "component": "view.manage_radar_exceptions",
                            "order": 4,
                            "icon": "mdi:bug-outline",
                            "status_type": StatusType.disable,
                        },
                        {
                            "menu_name": "系统监控",
                            "route_name": "manage_radar_monitor",
                            "route_path": "/manage/radar/monitor",
                            "component": "view.manage_radar_monitor",
                            "order": 5,
                            "icon": "mdi:monitor-dashboard",
                            "status_type": StatusType.disable,
                        },
                    ],
                },
            ],
        },
    ],
    "roles": [
        {
            "role_name": "管理员",
            "role_code": "R_ADMIN",
            "role_desc": "系统管理员，可维护用户/角色/菜单/API/字典/监控",
            "home_route": "home",
            "data_scope": DataScopeType.all,
            "menus": [
                "home",
                "user-center",
                "manage",
                "manage_user",
                "manage_user-detail",
                "manage_role",
                "manage_menu",
                "manage_api",
                "manage_codegen",
                "manage_radar",
                "manage_radar_overview",
                "manage_radar_requests",
                "manage_radar_queries",
                "manage_radar_exceptions",
                "manage_radar_monitor",
            ],
            "buttons": [],
            "apis": [
                # 用户
                *_crud_apis("users"),
                ("post", "/api/v1/system-manage/users/{user_id}/offline"),
                ("post", "/api/v1/system-manage/users/batch-offline"),
                # 角色
                *_crud_apis("roles"),
                ("get", "/api/v1/system-manage/roles/{role_id}/menus"),
                ("patch", "/api/v1/system-manage/roles/{role_id}/menus"),
                ("get", "/api/v1/system-manage/roles/{role_id}/buttons"),
                ("patch", "/api/v1/system-manage/roles/{role_id}/buttons"),
                ("get", "/api/v1/system-manage/roles/{role_id}/apis"),
                ("patch", "/api/v1/system-manage/roles/{role_id}/apis"),
                # 菜单
                *_crud_apis("menus"),
                ("get", "/api/v1/system-manage/menus/tree"),
                ("get", "/api/v1/system-manage/menus/pages"),
                ("get", "/api/v1/system-manage/menus/buttons/tree"),
                # API（资源由 refresh_api_list 全量对账，UI 仅只读）
                ("post", "/api/v1/system-manage/apis/search"),
                ("get", "/api/v1/system-manage/apis/tree"),
                ("get", "/api/v1/system-manage/apis/tags"),
                ("patch", "/api/v1/system-manage/apis/{api_id}/status"),
                # 字典
                ("get", "/api/v1/system-manage/dictionaries/{dict_type}/options"),
            ],
        },
        {
            "role_name": "普通用户",
            "role_code": "R_USER",
            "role_desc": "基础用户，仅可访问首页",
            "home_route": "home",
            "data_scope": DataScopeType.self_,
            "menus": ["home", "user-center"],
        },
    ],
    "users": [
        {"user_name": "Soybean", "user_email": "admin@admin.com", "password": "123456", "role_codes": [SUPER_ADMIN_ROLE]},
        {"user_name": "Super", "user_email": "admin1@admin.com", "password": "123456", "role_codes": [SUPER_ADMIN_ROLE]},
        {"user_name": "Admin", "user_email": "admin2@admin.com", "password": "123456", "role_codes": ["R_ADMIN"]},
        {"user_name": "User", "user_email": "user@user.com", "password": "123456", "role_codes": ["R_USER"]},
    ],
    # slim 分支不内置业务示例字典；业务模块可在自身 init_data 中声明。
    "dictionaries": [],
}


def build_system_init_data(*, radar_enabled: bool | None = None) -> dict:
    """按启动时的 Radar 开关生成菜单和角色种子，避免导入时配置快照漂移。"""
    enabled = APP_SETTINGS.RADAR_ENABLED if radar_enabled is None else radar_enabled
    init_data = deepcopy(SYSTEM_INIT_DATA)

    manage_menu = next(menu for menu in init_data["menus"] if menu["route_name"] == "manage")
    radar_menu = next(child for child in manage_menu["children"] if child["route_name"] == "manage_radar")
    radar_status = StatusType.enable if enabled else StatusType.disable
    radar_menu["status_type"] = radar_status
    for child in radar_menu["children"]:
        child["status_type"] = radar_status

    admin_role = next(role for role in init_data["roles"] if role["role_code"] == "R_ADMIN")
    if enabled:
        admin_role["apis"].extend(RADAR_API_REFS)

    return init_data


async def init_menus() -> None:
    init_data = build_system_init_data()
    await apply_init_data({"menus": init_data["menus"]})


async def _ensure_super_role() -> None:
    """同步超级管理员角色到最新菜单和按钮集合"""
    role_home_menu = await Menu.get(route_name="home")
    super_role, _ = await _safe_update_or_create(
        Role,
        {"role_code": SUPER_ADMIN_ROLE},
        {
            "role_name": "超级管理员",
            "role_desc": "超级管理员",
            "by_role_home": role_home_menu,
        },
    )

    await super_role.by_role_menus.clear()  # type: ignore[attr-defined]
    for menu_obj in await Menu.filter(constant=False):
        await super_role.by_role_menus.add(menu_obj)  # type: ignore[attr-defined]

    await super_role.by_role_buttons.clear()  # type: ignore[attr-defined]
    for button_obj in await Button.all():
        await super_role.by_role_buttons.add(button_obj)  # type: ignore[attr-defined]


async def init_users() -> None:
    init_data = build_system_init_data()
    await _ensure_super_role()
    await apply_init_data({
        "roles": init_data["roles"],
        "users": init_data["users"],
        "dictionaries": init_data["dictionaries"],
    })
