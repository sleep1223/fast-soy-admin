"""
labor_management 初始化数据 — 菜单、角色、种子数据。

启动时由 autodiscover 自动发现并执行 init()。
所有操作幂等，重复启动不会重复创建。
"""

from app.system.services import apply_init_data

INIT_DATA = {
    "menus": [
        {
            "menu_name": "劳务管理",
            "route_name": "labor-management",
            "route_path": "/labor-management",
            "order": 8,
            "icon": "mdi:application-cog-outline",
            "i18n_key": "route.labor-management",
            "reconcile": {"menus": True, "buttons": True},
            "children": [
                {
                    "menu_name": "劳务人员",
                    "route_name": "labor-management_labor-worker",
                    "route_path": "/labor-management/labor-worker",
                    "component": "view.labor-management_labor-worker",
                    "order": 1,
                    "icon": "mdi:table",
                    "i18n_key": "route.labor-management_labor-worker",
                    "buttons": [
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORKER_CREATE", "button_desc": "创建劳务人员"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORKER_EDIT", "button_desc": "编辑劳务人员"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORKER_DELETE", "button_desc": "删除劳务人员"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORKER_IMPORT", "button_desc": "导入劳务人员"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORKER_EXPORT", "button_desc": "导出劳务人员"},
                    ],
                },
                {
                    "menu_name": "工票对应的工时",
                    "route_name": "labor-management_labor-work-hour",
                    "route_path": "/labor-management/labor-work-hour",
                    "component": "view.labor-management_labor-work-hour",
                    "order": 2,
                    "icon": "mdi:table",
                    "i18n_key": "route.labor-management_labor-work-hour",
                    "buttons": [
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE", "button_desc": "创建工票对应的工时"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_EDIT", "button_desc": "编辑工票对应的工时"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_DELETE", "button_desc": "删除工票对应的工时"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_IMPORT", "button_desc": "导入工票对应的工时"},
                        {"button_code": "B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_EXPORT", "button_desc": "导出工票对应的工时"},
                    ],
                },
            ],
        }
    ],
    "roles": [],
    "users": [],
    "dictionaries": [],
}


async def init() -> None:
    """模块初始化入口 — 由 autodiscover 调用。"""
    await apply_init_data(INIT_DATA)
    # 普通角色要看到该菜单，请在角色管理中授权，或在这里补充 _init_role_data()。
    # await _init_role_data()
