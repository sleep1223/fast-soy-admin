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
            "menu_name": "关于",
            "route_name": "about",
            "route_path": "/about",
            "component": "layout.base$view.about",
            "order": 99,
            "icon": "fluent:book-information-24-regular",
        },
        {
            "menu_name": "功能",
            "route_name": "function",
            "route_path": "/function",
            "order": 2,
            "icon": "icon-park-outline:all-application",
            "children": [
                {"menu_name": "标签页", "route_name": "function_tab", "route_path": "/function/tab", "component": "view.function_tab", "order": 2, "icon": "ic:round-tab"},
                {
                    "menu_name": "多标签页",
                    "route_name": "function_multi-tab",
                    "route_path": "/function/multi-tab",
                    "component": "view.function_multi-tab",
                    "order": 1,
                    "icon": "ic:round-tab",
                    "multi_tab": True,
                    "hide_in_menu": True,
                    "active_menu": "function_tab",
                },
                {
                    "menu_name": "隐藏子菜单",
                    "route_name": "function_hide-child",
                    "route_path": "/function/hide-child",
                    "order": 2,
                    "icon": "material-symbols:filter-list-off",
                    "menu_type": "1",
                    "redirect": "/function/hide-child/one",
                    "children": [
                        {
                            "menu_name": "隐藏子菜单1",
                            "route_name": "function_hide-child_one",
                            "route_path": "/function/hide-child/one",
                            "component": "view.function_hide-child_one",
                            "order": 1,
                            "icon": "material-symbols:filter-list-off",
                            "hide_in_menu": True,
                            "active_menu": "function_hide-child",
                        },
                        {
                            "menu_name": "隐藏子菜单2",
                            "route_name": "function_hide-child_two",
                            "route_path": "/function/hide-child/two",
                            "component": "view.function_hide-child_two",
                            "order": 2,
                            "hide_in_menu": True,
                            "active_menu": "function_hide-child",
                        },
                        {
                            "menu_name": "隐藏子菜单3",
                            "route_name": "function_hide-child_three",
                            "route_path": "/function/hide-child/three",
                            "component": "view.function_hide-child_three",
                            "order": 3,
                            "hide_in_menu": True,
                            "active_menu": "function_hide-child",
                        },
                    ],
                },
                {"menu_name": "请求", "route_name": "function_request", "route_path": "/function/request", "component": "view.function_request", "order": 3, "icon": "carbon:network-overlay"},
                {
                    "menu_name": "切换权限",
                    "route_name": "function_toggle-auth",
                    "route_path": "/function/toggle-auth",
                    "component": "view.function_toggle-auth",
                    "order": 4,
                    "icon": "ic:round-construction",
                    "buttons": [
                        {"button_code": "B_CODE1", "button_desc": "超级管理员可见"},
                        {"button_code": "B_CODE2", "button_desc": "管理员可见"},
                        {"button_code": "B_CODE3", "button_desc": "管理员和用户可见"},
                    ],
                },
                {
                    "menu_name": "超级管理员可见",
                    "route_name": "function_super-page",
                    "route_path": "/function/super-page",
                    "component": "view.function_super-page",
                    "order": 5,
                    "icon": "ic:round-supervisor-account",
                },
            ],
        },
        {
            "menu_name": "异常页",
            "route_name": "exception",
            "route_path": "/exception",
            "order": 3,
            "icon": "ant-design:exception-outlined",
            "children": [
                {"menu_name": "403", "route_name": "exception_403", "route_path": "/exception/403", "component": "view.403", "order": 1, "icon": "ic:baseline-block"},
                {"menu_name": "404", "route_name": "exception_404", "route_path": "/exception/404", "component": "view.404", "order": 2, "icon": "ic:baseline-web-asset-off"},
                {"menu_name": "500", "route_name": "exception_500", "route_path": "/exception/500", "component": "view.500", "order": 3, "icon": "ic:baseline-wifi-off"},
            ],
        },
        {
            "menu_name": "多级菜单",
            "route_name": "multi-menu",
            "route_path": "/multi-menu",
            "order": 4,
            "icon": "mdi:menu",
            "children": [
                {
                    "menu_name": "一级子菜单1",
                    "route_name": "multi-menu_first",
                    "route_path": "/multi-menu/first",
                    "order": 1,
                    "icon": "mdi:menu",
                    "menu_type": "1",
                    "children": [
                        {
                            "menu_name": "二级子菜单",
                            "route_name": "multi-menu_first_child",
                            "route_path": "/multi-menu/first/child",
                            "component": "view.multi-menu_first_child",
                            "order": 1,
                            "icon": "mdi:menu",
                        },
                    ],
                },
                {
                    "menu_name": "一级子菜单2",
                    "route_name": "multi-menu_second",
                    "route_path": "/multi-menu/second",
                    "order": 13,
                    "icon": "mdi:menu",
                    "menu_type": "1",
                    "children": [
                        {
                            "menu_name": "二级子菜单2",
                            "route_name": "multi-menu_second_child",
                            "route_path": "/multi-menu/second/child",
                            "order": 1,
                            "icon": "mdi:menu",
                            "menu_type": "1",
                            "children": [
                                {
                                    "menu_name": "三级菜单",
                                    "route_name": "multi-menu_second_child_home",
                                    "route_path": "/multi-menu/second/child/home",
                                    "component": "view.multi-menu_second_child_home",
                                    "order": 1,
                                    "icon": "mdi:menu",
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "menu_name": "系统管理",
            "route_name": "manage",
            "route_path": "/manage",
            "order": 5,
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
        {
            "menu_name": "alova示例",
            "route_name": "alova",
            "route_path": "/alova",
            "order": 7,
            "icon": "carbon:http",
            "children": [
                {"menu_name": "alova_request", "route_name": "alova_request", "route_path": "/alova/request", "component": "view.alova_request", "order": 1, "icon": "ic:baseline-block"},
                {"menu_name": "alova_scenes", "route_name": "alova_scenes", "route_path": "/alova/scenes", "component": "view.alova_scenes", "order": 2, "icon": "cbi:scene-dynamic"},
            ],
        },
        {
            "menu_name": "插件示例",
            "route_name": "plugin",
            "route_path": "/plugin",
            "order": 7,
            "icon": "clarity:plugin-line",
            "children": [
                {"menu_name": "plugin_barcode", "route_name": "plugin_barcode", "route_path": "/plugin/barcode", "component": "view.plugin_barcode", "order": 1, "icon": "ic:round-barcode"},
                {
                    "menu_name": "plugin_charts",
                    "route_name": "plugin_charts",
                    "route_path": "/plugin/charts",
                    "order": 2,
                    "icon": "mdi:chart-areaspline",
                    "menu_type": "1",
                    "children": [
                        {
                            "menu_name": "plugin_charts_antv",
                            "route_name": "plugin_charts_antv",
                            "route_path": "/plugin/charts/antv",
                            "component": "view.plugin_charts_antv",
                            "order": 1,
                            "icon": "hugeicons:flow-square",
                        },
                        {
                            "menu_name": "plugin_charts_echarts",
                            "route_name": "plugin_charts_echarts",
                            "route_path": "/plugin/charts/echarts",
                            "component": "view.plugin_charts_echarts",
                            "order": 2,
                            "icon": "simple-icons:apacheecharts",
                        },
                        {
                            "menu_name": "plugin_charts_vchart",
                            "route_name": "plugin_charts_vchart",
                            "route_path": "/plugin/charts/vchart",
                            "component": "view.plugin_charts_vchart",
                            "order": 3,
                            "icon": "visactor",
                            "icon_type": "2",
                        },
                    ],
                },
                {"menu_name": "plugin_copy", "route_name": "plugin_copy", "route_path": "/plugin/copy", "component": "view.plugin_copy", "order": 3, "icon": "mdi:clipboard-outline"},
                {
                    "menu_name": "plugin_editor",
                    "route_name": "plugin_editor",
                    "route_path": "/plugin/editor",
                    "order": 4,
                    "icon": "icon-park-outline:editor",
                    "menu_type": "1",
                    "children": [
                        {
                            "menu_name": "plugin_editor_markdown",
                            "route_name": "plugin_editor_markdown",
                            "route_path": "/plugin/editor/markdown",
                            "component": "view.plugin_editor_markdown",
                            "order": 1,
                            "icon": "ri:markdown-line",
                        },
                        {
                            "menu_name": "plugin_editor_quill",
                            "route_name": "plugin_editor_quill",
                            "route_path": "/plugin/editor/quill",
                            "component": "view.plugin_editor_quill",
                            "order": 2,
                            "icon": "mdi:file-document-edit-outline",
                        },
                    ],
                },
                {"menu_name": "plugin_excel", "route_name": "plugin_excel", "route_path": "/plugin/excel", "component": "view.plugin_excel", "order": 5, "icon": "ri:file-excel-2-line"},
                {
                    "menu_name": "plugin_gantt",
                    "route_name": "plugin_gantt",
                    "route_path": "/plugin/gantt",
                    "order": 6,
                    "icon": "ant-design:bar-chart-outlined",
                    "menu_type": "1",
                    "children": [
                        {"menu_name": "plugin_gantt_dhtmlx", "route_name": "plugin_gantt_dhtmlx", "route_path": "/plugin/gantt/dhtmlx", "component": "view.plugin_gantt_dhtmlx", "order": 1},
                        {
                            "menu_name": "plugin_gantt_vtable",
                            "route_name": "plugin_gantt_vtable",
                            "route_path": "/plugin/gantt/vtable",
                            "component": "view.plugin_gantt_vtable",
                            "order": 2,
                            "icon": "visactor",
                            "icon_type": "2",
                        },
                    ],
                },
                {"menu_name": "plugin_icon", "route_name": "plugin_icon", "route_path": "/plugin/icon", "component": "view.plugin_icon", "order": 7, "icon": "custom-icon", "icon_type": "2"},
                {"menu_name": "plugin_map", "route_name": "plugin_map", "route_path": "/plugin/map", "component": "view.plugin_map", "order": 8, "icon": "mdi:map"},
                {"menu_name": "plugin_pdf", "route_name": "plugin_pdf", "route_path": "/plugin/pdf", "component": "view.plugin_pdf", "order": 9, "icon": "uiw:file-pdf"},
                {"menu_name": "plugin_pinyin", "route_name": "plugin_pinyin", "route_path": "/plugin/pinyin", "component": "view.plugin_pinyin", "order": 10, "icon": "entypo-social:google-hangouts"},
                {"menu_name": "plugin_print", "route_name": "plugin_print", "route_path": "/plugin/print", "component": "view.plugin_print", "order": 11, "icon": "mdi:printer"},
                {"menu_name": "plugin_swiper", "route_name": "plugin_swiper", "route_path": "/plugin/swiper", "component": "view.plugin_swiper", "order": 12, "icon": "simple-icons:swiper"},
                {
                    "menu_name": "plugin_tables",
                    "route_name": "plugin_tables",
                    "route_path": "/plugin/tables",
                    "order": 13,
                    "icon": "icon-park-outline:table",
                    "menu_type": "1",
                    "children": [
                        {
                            "menu_name": "plugin_tables_vtable",
                            "route_name": "plugin_tables_vtable",
                            "route_path": "/plugin/tables/vtable",
                            "component": "view.plugin_tables_vtable",
                            "order": 1,
                            "icon": "visactor",
                            "icon_type": "2",
                        },
                    ],
                },
                {"menu_name": "plugin_typeit", "route_name": "plugin_typeit", "route_path": "/plugin/typeit", "component": "view.plugin_typeit", "order": 14, "icon": "mdi:typewriter"},
                {"menu_name": "plugin_video", "route_name": "plugin_video", "route_path": "/plugin/video", "component": "view.plugin_video", "order": 15, "icon": "mdi:video"},
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
                "about",
                "function",
                "function_multi-tab",
                "function_hide-child",
                "function_hide-child_one",
                "function_hide-child_two",
                "function_hide-child_three",
                "function_tab",
                "function_request",
                "function_toggle-auth",
                "function_super-page",
                "exception",
                "exception_403",
                "exception_404",
                "exception_500",
                "multi-menu",
                "multi-menu_first",
                "multi-menu_first_child",
                "multi-menu_second",
                "multi-menu_second_child",
                "multi-menu_second_child_home",
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
                "alova",
                "alova_request",
                "alova_scenes",
                "plugin",
                "plugin_barcode",
                "plugin_charts",
                "plugin_charts_antv",
                "plugin_charts_echarts",
                "plugin_charts_vchart",
                "plugin_copy",
                "plugin_editor",
                "plugin_editor_markdown",
                "plugin_editor_quill",
                "plugin_excel",
                "plugin_gantt",
                "plugin_gantt_dhtmlx",
                "plugin_gantt_vtable",
                "plugin_icon",
                "plugin_map",
                "plugin_pdf",
                "plugin_pinyin",
                "plugin_print",
                "plugin_swiper",
                "plugin_tables",
                "plugin_tables_vtable",
                "plugin_typeit",
                "plugin_video",
            ],
            "buttons": ["B_CODE2", "B_CODE3"],
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
            "menus": ["home", "about", "user-center"],
        },
    ],
    "users": [
        {"user_name": "Soybean", "user_email": "admin@admin.com", "password": "123456", "role_codes": [SUPER_ADMIN_ROLE]},
        {"user_name": "Super", "user_email": "admin1@admin.com", "password": "123456", "role_codes": [SUPER_ADMIN_ROLE]},
        {"user_name": "Admin", "user_email": "admin2@admin.com", "password": "123456", "role_codes": ["R_ADMIN"]},
        {"user_name": "User", "user_email": "user@user.com", "password": "123456", "role_codes": ["R_USER"]},
    ],
    "dictionaries": [
        {"dict_type": "tag_category", "label": "工作方式", "value": "working_style", "order": 1},
        {"dict_type": "tag_category", "label": "协作习惯", "value": "collaboration", "order": 2},
        {"dict_type": "tag_category", "label": "团队角色", "value": "team_role", "order": 3},
        {"dict_type": "tag_category", "label": "业务方向", "value": "business", "order": 4},
        {"dict_type": "tag_category", "label": "成长方向", "value": "growth", "order": 5},
        {"dict_type": "employee_position", "label": "技术主管", "value": "tech_lead", "order": 1},
        {"dict_type": "employee_position", "label": "前端工程师", "value": "frontend_engineer", "order": 2},
        {"dict_type": "employee_position", "label": "后端工程师", "value": "backend_engineer", "order": 3},
        {"dict_type": "employee_position", "label": "市场主管", "value": "marketing_lead", "order": 4},
        {"dict_type": "employee_position", "label": "市场专员", "value": "marketing_specialist", "order": 5},
        {"dict_type": "employee_position", "label": "行政专员", "value": "admin_specialist", "order": 6},
    ],
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
