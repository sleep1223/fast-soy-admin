"""
work_ticket_management 管理接口 — 基础资料 CRUD 与聚合资源只读查询。

工票、导入、工时、月度状态等聚合写操作在 services/ 与专用 API 中实现；
这里不注册它们的通用写路由，也不注册聚合 Excel 导入，避免绕过业务校验。
"""

from fastapi import APIRouter

from app.business.work_ticket_management.controllers import (
    monthly_import_batch_controller,
    monthly_import_row_controller,
    order_unit_mapping_controller,
    production_unit_controller,
    work_month_controller,
    work_month_status_log_controller,
    work_ticket_assignment_controller,
    work_ticket_controller,
    work_time_entry_controller,
    worker_controller,
)
from app.business.work_ticket_management.schemas import (
    MonthlyImportBatchSearch,
    MonthlyImportRowSearch,
    OrderUnitMappingCreate,
    OrderUnitMappingSearch,
    OrderUnitMappingUpdate,
    ProductionUnitCreate,
    ProductionUnitSearch,
    ProductionUnitUpdate,
    WorkerCreate,
    WorkerSearch,
    WorkerUpdate,
    WorkMonthSearch,
    WorkMonthStatusLogSearch,
    WorkTicketAssignmentSearch,
    WorkTicketSearch,
    WorkTimeEntrySearch,
)
from app.utils import CRUDRouter, ExcelConfig, SearchFieldConfig, require_buttons

production_unit_crud = CRUDRouter(
    prefix="/production_units",
    controller=production_unit_controller,
    create_schema=ProductionUnitCreate,
    excel=ExcelConfig(fields=("code", "name", "enabled", "remark"), update_key="code"),
    update_schema=ProductionUnitUpdate,
    list_schema=ProductionUnitSearch,
    route_key_prefix="work_ticket_management.production_units",
    search_fields=SearchFieldConfig(contains_fields=["code", "name", "remark"], exact_fields=["enabled"]),
    action_dependencies={
        "create": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_CREATE")],
        "update": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_EDIT")],
        "delete": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_DELETE")],
        "batch_delete": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_DELETE")],
        "import": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_IMPORT")],
        "import_template": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_IMPORT")],
        "export": [require_buttons("B_WORK_TICKET_MANAGEMENT_PRODUCTION_UNIT_EXPORT")],
    },
    summary_prefix="生产单位",
)

worker_crud = CRUDRouter(
    prefix="/workers",
    controller=worker_controller,
    create_schema=WorkerCreate,
    excel=ExcelConfig(fields=("worker_no", "name", "enabled", "remark", "production_unit_id"), update_key="id"),
    update_schema=WorkerUpdate,
    list_schema=WorkerSearch,
    route_key_prefix="work_ticket_management.workers",
    search_fields=SearchFieldConfig(contains_fields=["worker_no", "name", "remark"], exact_fields=["enabled", "production_unit_id"]),
    action_dependencies={
        "create": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_CREATE")],
        "update": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_EDIT")],
        "delete": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_DELETE")],
        "batch_delete": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_DELETE")],
        "import": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_IMPORT")],
        "import_template": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_IMPORT")],
        "export": [require_buttons("B_WORK_TICKET_MANAGEMENT_WORKER_EXPORT")],
    },
    summary_prefix="生产人员",
)

order_unit_mapping_crud = CRUDRouter(
    prefix="/order_unit_mappings",
    controller=order_unit_mapping_controller,
    create_schema=OrderUnitMappingCreate,
    update_schema=OrderUnitMappingUpdate,
    list_schema=OrderUnitMappingSearch,
    route_key_prefix="work_ticket_management.order_unit_mappings",
    search_fields=SearchFieldConfig(contains_fields=["remark"], exact_fields=["order_id", "production_unit_id"]),
    action_dependencies={
        "create": [require_buttons("B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_CREATE")],
        "update": [require_buttons("B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_EDIT")],
        "delete": [require_buttons("B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_DELETE")],
        "batch_delete": [require_buttons("B_WORK_TICKET_MANAGEMENT_ORDER_UNIT_MAPPING_DELETE")],
    },
    summary_prefix="订单与生产单位关系",
)

work_month_crud = CRUDRouter(
    prefix="/work_months",
    controller=work_month_controller,
    list_schema=WorkMonthSearch,
    route_key_prefix="work_ticket_management.work_months",
    search_fields=SearchFieldConfig(contains_fields=["year_month", "remark", "closed_by"], exact_fields=["status", "production_unit_id"], range_fields=["closed_at", "reopened_at"]),
    enable_routes={"list", "get"},
    summary_prefix="月度任务",
)

monthly_import_batch_crud = CRUDRouter(
    prefix="/monthly_import_batches",
    controller=monthly_import_batch_controller,
    list_schema=MonthlyImportBatchSearch,
    route_key_prefix="work_ticket_management.monthly_import_batches",
    search_fields=SearchFieldConfig(
        contains_fields=["source_name", "content_hash", "void_reason", "voided_by", "remark"],
        exact_fields=["source_type", "status", "work_month_id"],
        range_fields=["voided_at"],
    ),
    enable_routes={"list", "get"},
    summary_prefix="月度导入批次",
)

monthly_import_row_crud = CRUDRouter(
    prefix="/monthly_import_rows",
    controller=monthly_import_row_controller,
    list_schema=MonthlyImportRowSearch,
    route_key_prefix="work_ticket_management.monthly_import_rows",
    search_fields=SearchFieldConfig(
        contains_fields=["raw_part_no", "normalized_part_no", "handling_note", "handled_by", "note"],
        exact_fields=["match_status", "match_source", "handling_status", "batch_id", "order_id", "duplicate_of_row_id"],
        range_fields=["handled_at"],
    ),
    enable_routes={"list", "get"},
    summary_prefix="导入原始明细",
)

work_ticket_crud = CRUDRouter(
    prefix="/work_tickets",
    controller=work_ticket_controller,
    list_schema=WorkTicketSearch,
    route_key_prefix="work_ticket_management.work_tickets",
    search_fields=SearchFieldConfig(
        contains_fields=["order_no_snapshot", "part_no_snapshot", "name_snapshot", "ticket_code", "ticket_code_key", "code_rule_version", "reconcile_note", "void_reason", "voided_by", "remark"],
        exact_fields=["code_source", "status", "reconcile_status", "work_month_id", "order_id", "source_import_row_id"],
        range_fields=["voided_at"],
    ),
    enable_routes={"list", "get"},
    summary_prefix="工票台账",
)

work_ticket_assignment_crud = CRUDRouter(
    prefix="/work_ticket_assignments",
    controller=work_ticket_assignment_controller,
    list_schema=WorkTicketAssignmentSearch,
    route_key_prefix="work_ticket_management.work_ticket_assignments",
    search_fields=SearchFieldConfig(contains_fields=["remark"], exact_fields=["source", "ticket_id", "worker_id"]),
    enable_routes={"list", "get"},
    summary_prefix="工票人员分配",
)

work_time_entry_crud = CRUDRouter(
    prefix="/work_time_entries",
    controller=work_time_entry_controller,
    list_schema=WorkTimeEntrySearch,
    route_key_prefix="work_ticket_management.work_time_entries",
    search_fields=SearchFieldConfig(contains_fields=["accounting_month", "remark"], exact_fields=["assignment_id"], range_fields=["work_date"]),
    enable_routes={"list", "get"},
    summary_prefix="工时明细",
)

work_month_status_log_crud = CRUDRouter(
    prefix="/work_month_status_logs",
    controller=work_month_status_log_controller,
    list_schema=WorkMonthStatusLogSearch,
    route_key_prefix="work_ticket_management.work_month_status_logs",
    search_fields=SearchFieldConfig(contains_fields=["reason"], exact_fields=["from_status", "to_status", "action", "work_month_id"]),
    enable_routes={"list", "get"},
    summary_prefix="月度状态日志",
)

router = APIRouter(tags=["work_ticket_management"])
router.include_router(production_unit_crud.router)
router.include_router(worker_crud.router)
router.include_router(order_unit_mapping_crud.router)
router.include_router(work_month_crud.router)
router.include_router(monthly_import_batch_crud.router)
router.include_router(monthly_import_row_crud.router)
router.include_router(work_ticket_crud.router)
router.include_router(work_ticket_assignment_crud.router)
router.include_router(work_time_entry_crud.router)
router.include_router(work_month_status_log_crud.router)
