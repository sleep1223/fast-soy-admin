"""
work_ticket_management 初始化数据 — 菜单、角色、种子数据。

启动时由 autodiscover 自动发现并执行 init()。
所有操作幂等，重复启动不会重复创建。
"""

from app.system.services import apply_init_data

INIT_DATA = {
    "menus": [
        {
            "menu_name": "work_ticket_management",
            "route_name": "work-ticket-management",
            "route_path": "/work-ticket-management",
            "order": 8,
            "icon": "mdi:application-cog-outline",
            "i18n_key": "route.work-ticket-management",
            "reconcile": {"menus": True, "buttons": True},
            "children": [
                {
                    "menu_name": "生产单位",
                    "route_name": "work-ticket-management_production-unit",
                    "route_path": "/work-ticket-management/production-unit",
                    "component": "view.work-ticket-management_production-unit",
                    "order": 1,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_production-unit",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_CREATE", "button_desc": "创建生产单位"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_EDIT", "button_desc": "编辑生产单位"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_DELETE", "button_desc": "删除生产单位"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_IMPORT", "button_desc": "导入生产单位"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_EXPORT", "button_desc": "导出生产单位"},
                    ],
                },
                {
                    "menu_name": "生产人员",
                    "route_name": "work-ticket-management_worker",
                    "route_path": "/work-ticket-management/worker",
                    "component": "view.work-ticket-management_worker",
                    "order": 2,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_worker",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORKER_CREATE", "button_desc": "创建生产人员"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORKER_EDIT", "button_desc": "编辑生产人员"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORKER_DELETE", "button_desc": "删除生产人员"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORKER_IMPORT", "button_desc": "导入生产人员"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORKER_EXPORT", "button_desc": "导出生产人员"},
                    ],
                },
                {
                    "menu_name": "订单与生产单位关系",
                    "route_name": "work-ticket-management_order-unit-mapping",
                    "route_path": "/work-ticket-management/order-unit-mapping",
                    "component": "view.work-ticket-management_order-unit-mapping",
                    "order": 3,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_order-unit-mapping",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_CREATE", "button_desc": "创建订单与生产单位关系"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_EDIT", "button_desc": "编辑订单与生产单位关系"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_DELETE", "button_desc": "删除订单与生产单位关系"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_IMPORT", "button_desc": "导入订单与生产单位关系"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_EXPORT", "button_desc": "导出订单与生产单位关系"},
                    ],
                },
                {
                    "menu_name": "月度任务",
                    "route_name": "work-ticket-management_work-month",
                    "route_path": "/work-ticket-management/work-month",
                    "component": "view.work-ticket-management_work-month",
                    "order": 4,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_work-month",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_CREATE", "button_desc": "创建月度任务"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_EDIT", "button_desc": "编辑月度任务"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_DELETE", "button_desc": "删除月度任务"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_IMPORT", "button_desc": "导入月度任务"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_EXPORT", "button_desc": "导出月度任务"},
                    ],
                },
                {
                    "menu_name": "月度导入批次",
                    "route_name": "work-ticket-management_monthly-import-batch",
                    "route_path": "/work-ticket-management/monthly-import-batch",
                    "component": "view.work-ticket-management_monthly-import-batch",
                    "order": 5,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_monthly-import-batch",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_BATCH_CREATE", "button_desc": "创建月度导入批次"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_BATCH_EDIT", "button_desc": "编辑月度导入批次"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_BATCH_DELETE", "button_desc": "删除月度导入批次"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_BATCH_IMPORT", "button_desc": "导入月度导入批次"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_BATCH_EXPORT", "button_desc": "导出月度导入批次"},
                    ],
                },
                {
                    "menu_name": "导入原始明细",
                    "route_name": "work-ticket-management_monthly-import-row",
                    "route_path": "/work-ticket-management/monthly-import-row",
                    "component": "view.work-ticket-management_monthly-import-row",
                    "order": 6,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_monthly-import-row",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_ROW_CREATE", "button_desc": "创建导入原始明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_ROW_EDIT", "button_desc": "编辑导入原始明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_ROW_DELETE", "button_desc": "删除导入原始明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_ROW_IMPORT", "button_desc": "导入导入原始明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_MONTHLY_IMPORT_ROW_EXPORT", "button_desc": "导出导入原始明细"},
                    ],
                },
                {
                    "menu_name": "工票台账",
                    "route_name": "work-ticket-management_work-ticket",
                    "route_path": "/work-ticket-management/work-ticket",
                    "component": "view.work-ticket-management_work-ticket",
                    "order": 7,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_work-ticket",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_CREATE", "button_desc": "创建工票台账"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_EDIT", "button_desc": "编辑工票台账"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_DELETE", "button_desc": "删除工票台账"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_IMPORT", "button_desc": "导入工票台账"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_EXPORT", "button_desc": "导出工票台账"},
                    ],
                },
                {
                    "menu_name": "工票人员分配",
                    "route_name": "work-ticket-management_work-ticket-assignment",
                    "route_path": "/work-ticket-management/work-ticket-assignment",
                    "component": "view.work-ticket-management_work-ticket-assignment",
                    "order": 8,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_work-ticket-assignment",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_ASSIGNMENT_CREATE", "button_desc": "创建工票人员分配"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_ASSIGNMENT_EDIT", "button_desc": "编辑工票人员分配"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_ASSIGNMENT_DELETE", "button_desc": "删除工票人员分配"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_ASSIGNMENT_IMPORT", "button_desc": "导入工票人员分配"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TICKET_ASSIGNMENT_EXPORT", "button_desc": "导出工票人员分配"},
                    ],
                },
                {
                    "menu_name": "工时明细",
                    "route_name": "work-ticket-management_work-time-entry",
                    "route_path": "/work-ticket-management/work-time-entry",
                    "component": "view.work-ticket-management_work-time-entry",
                    "order": 9,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_work-time-entry",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TIME_ENTRY_CREATE", "button_desc": "创建工时明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TIME_ENTRY_EDIT", "button_desc": "编辑工时明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TIME_ENTRY_DELETE", "button_desc": "删除工时明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TIME_ENTRY_IMPORT", "button_desc": "导入工时明细"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_TIME_ENTRY_EXPORT", "button_desc": "导出工时明细"},
                    ],
                },
                {
                    "menu_name": "月度状态日志",
                    "route_name": "work-ticket-management_work-month-status-log",
                    "route_path": "/work-ticket-management/work-month-status-log",
                    "component": "view.work-ticket-management_work-month-status-log",
                    "order": 10,
                    "icon": "mdi:table",
                    "i18n_key": "route.work-ticket-management_work-month-status-log",
                    "buttons": [
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_STATUS_LOG_CREATE", "button_desc": "创建月度状态日志"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_STATUS_LOG_EDIT", "button_desc": "编辑月度状态日志"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_STATUS_LOG_DELETE", "button_desc": "删除月度状态日志"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_STATUS_LOG_IMPORT", "button_desc": "导入月度状态日志"},
                        {"button_code": "B_WORK_TICKET_MANAGEMENT_WORK_MONTH_STATUS_LOG_EXPORT", "button_desc": "导出月度状态日志"},
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
