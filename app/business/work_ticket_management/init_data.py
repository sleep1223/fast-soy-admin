"""
work_ticket_management 初始化数据 — 菜单、按钮。

启动时由 autodiscover 自动发现并执行 init()。
启用 reconcile 后，本模块菜单子树以这里为唯一数据源；Web 端手工新增的
子菜单/按钮会在下次启动时被清理。
"""

from app.business.work_ticket_management.constants import (
    B_IMPORT_ACTUAL,
    B_IMPORT_MANUAL,
    B_IMPORT_PLAN,
    B_IMPORT_ROW_EDIT,
    B_IMPORT_ROW_IGNORE,
    B_IMPORT_ROW_MATCH,
    B_IMPORT_VOID,
    B_MAPPING_CREATE,
    B_MAPPING_DELETE,
    B_MAPPING_EDIT,
    B_MONTH_CLOSE,
    B_MONTH_EXPORT,
    B_MONTH_OPEN,
    B_MONTH_REOPEN,
    B_MONTH_VERIFY,
    B_PRODUCTION_UNIT_CREATE,
    B_PRODUCTION_UNIT_DELETE,
    B_PRODUCTION_UNIT_EDIT,
    B_PRODUCTION_UNIT_EXPORT,
    B_PRODUCTION_UNIT_IMPORT,
    B_REPORT_EXPORT,
    B_TICKET_ASSIGN,
    B_TICKET_CODE,
    B_TICKET_CREATE,
    B_TICKET_EDIT,
    B_TICKET_EXPORT,
    B_TICKET_OCR,
    B_TICKET_RECONCILE,
    B_TICKET_VOID,
    B_TIME_DELETE,
    B_TIME_EDIT,
    B_TIME_EXPORT,
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
    _button(B_MONTH_VERIFY, "核对月度任务"),
    _button(B_MONTH_CLOSE, "关闭月度任务"),
    _button(B_MONTH_REOPEN, "重新打开月度任务"),
    _button(B_MONTH_EXPORT, "导出月度工作簿"),
    _button(B_IMPORT_PLAN, "导入计划清单"),
    _button(B_IMPORT_ACTUAL, "导入实际入库清单"),
    _button(B_IMPORT_MANUAL, "手工补录导入行"),
    _button(B_IMPORT_VOID, "作废导入批次"),
    _button(B_IMPORT_ROW_EDIT, "修改导入行"),
    _button(B_IMPORT_ROW_MATCH, "确认导入行订单"),
    _button(B_IMPORT_ROW_IGNORE, "忽略导入行"),
]

TICKET_BUTTONS = [
    _button(B_TICKET_CREATE, "创建工票"),
    _button(B_TICKET_EDIT, "编辑工票"),
    _button(B_TICKET_VOID, "作废工票"),
    _button(B_TICKET_ASSIGN, "分配工票人员"),
    _button(B_TICKET_CODE, "录入或生成工票码"),
    _button(B_TICKET_OCR, "OCR 识别工票码"),
    _button(B_TICKET_RECONCILE, "标记工票核对"),
    _button(B_TICKET_EXPORT, "导出工票"),
]

TIME_BUTTONS = [
    _button(B_TIME_EDIT, "登记或修改工时"),
    _button(B_TIME_DELETE, "删除工时"),
    _button(B_TIME_EXPORT, "导出工时"),
]

MASTER_DATA_BUTTONS = [
    _button(B_PRODUCTION_UNIT_CREATE, "创建生产单位"),
    _button(B_PRODUCTION_UNIT_EDIT, "编辑生产单位"),
    _button(B_PRODUCTION_UNIT_DELETE, "删除生产单位"),
    _button(B_PRODUCTION_UNIT_IMPORT, "导入生产单位"),
    _button(B_PRODUCTION_UNIT_EXPORT, "导出生产单位"),
    _button(B_WORKER_CREATE, "创建生产人员"),
    _button(B_WORKER_EDIT, "编辑生产人员"),
    _button(B_WORKER_DELETE, "删除生产人员"),
    _button(B_WORKER_IMPORT, "导入生产人员"),
    _button(B_WORKER_EXPORT, "导出生产人员"),
    _button(B_MAPPING_CREATE, "新增订单单位关联"),
    _button(B_MAPPING_EDIT, "编辑订单单位关联"),
    _button(B_MAPPING_DELETE, "删除订单单位关联"),
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
                    "menu_name": "工票台账",
                    "route_name": "work-ticket-management_tickets",
                    "route_path": "/work-ticket-management/tickets",
                    "component": "view.work-ticket-management_tickets",
                    "order": 2,
                    "icon": "mdi:card-account-details-outline",
                    "i18n_key": "route.work-ticket-management_tickets",
                    "buttons": TICKET_BUTTONS,
                },
                {
                    "menu_name": "工时登记",
                    "route_name": "work-ticket-management_time-entries",
                    "route_path": "/work-ticket-management/time-entries",
                    "component": "view.work-ticket-management_time-entries",
                    "order": 3,
                    "icon": "mdi:clock-edit-outline",
                    "i18n_key": "route.work-ticket-management_time-entries",
                    "buttons": TIME_BUTTONS,
                },
                {
                    "menu_name": "月度核对",
                    "route_name": "work-ticket-management_reconciliation",
                    "route_path": "/work-ticket-management/reconciliation",
                    "component": "view.work-ticket-management_reconciliation",
                    "order": 4,
                    "icon": "mdi:check-decagram-outline",
                    "i18n_key": "route.work-ticket-management_reconciliation",
                },
                {
                    "menu_name": "统计报表",
                    "route_name": "work-ticket-management_reports",
                    "route_path": "/work-ticket-management/reports",
                    "component": "view.work-ticket-management_reports",
                    "order": 5,
                    "icon": "mdi:chart-box-outline",
                    "i18n_key": "route.work-ticket-management_reports",
                    "buttons": [_button(B_REPORT_EXPORT, "导出统计报表")],
                },
                {
                    "menu_name": "人员与生产单位",
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
