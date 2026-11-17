"""
work_ticket_management 初始化数据 — 菜单、按钮。

启动时由 autodiscover 自动发现并执行 init()。
启用 reconcile 后，本模块菜单子树以这里为唯一数据源；Web 端手工新增的
子菜单/按钮会在下次启动时被清理。
"""

from app.business.work_ticket_management.constants import (
    B_IMPORT_ACTUAL,
    B_IMPORT_PLAN,
    B_MONTH_OPEN,
    B_TICKET_CREATE,
    B_TICKET_OCR,
    B_TIME_EDIT,
    B_WORKER_CREATE,
    B_WORKER_DELETE,
    B_WORKER_EDIT,
    B_WORKER_EXPORT,
    B_WORKER_IMPORT,
)
from app.system.services import apply_init_data


def _button(code: str, desc: str) -> dict[str, str]:
    return {"button_code": code, "button_desc": desc}


WORKBENCH_BUTTONS = [
    _button(B_MONTH_OPEN, "打开月度任务"),
    _button(B_IMPORT_PLAN, "导入当月件号"),
    _button(B_IMPORT_ACTUAL, "补录遗漏件号"),
    _button(B_TICKET_CREATE, "创建工票"),
    _button(B_TICKET_OCR, "OCR 识别工票码"),
    _button(B_TIME_EDIT, "登记或修改工时"),
]

MASTER_DATA_BUTTONS = [
    _button(B_WORKER_CREATE, "创建生产人员"),
    _button(B_WORKER_EDIT, "编辑生产人员"),
    _button(B_WORKER_DELETE, "删除生产人员"),
    _button(B_WORKER_IMPORT, "导入生产人员"),
    _button(B_WORKER_EXPORT, "导出生产人员"),
]

INIT_DATA = {
    "menus": [
        {
            "menu_name": "工票工时管理",
            "route_name": "work-ticket-management",
            "route_path": "/work-ticket-management",
            "order": 9,
            "icon": "mdi:clipboard-text-clock-outline",
            "i18n_key": "route.work-ticket-management",
            "reconcile": {"menus": True, "buttons": True},
            "children": [
                {
                    "menu_name": "月度工作台",
                    "route_name": "work-ticket-management_workbench",
                    "route_path": "/work-ticket-management/workbench",
                    "component": "view.work-ticket-management_workbench",
                    "order": 1,
                    "icon": "mdi:view-dashboard-outline",
                    "i18n_key": "route.work-ticket-management_workbench",
                    "buttons": WORKBENCH_BUTTONS,
                },
                {
                    "menu_name": "人员管理",
                    "route_name": "work-ticket-management_master-data",
                    "route_path": "/work-ticket-management/master-data",
                    "component": "view.work-ticket-management_master-data",
                    "order": 6,
                    "icon": "mdi:account-hard-hat-outline",
                    "i18n_key": "route.work-ticket-management_master-data",
                    "buttons": MASTER_DATA_BUTTONS,
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
    # 角色授权：建议在角色管理中把菜单/按钮/API 授予实际使用角色；
    # 单人使用时 R_SUPER 已自动获得全部权限。
