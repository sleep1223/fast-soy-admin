"""
labor_management 管理接口 — CRUD。
"""

from fastapi import APIRouter

from app.business.labor_management.controllers import labor_work_hour_controller, labor_worker_controller
from app.business.labor_management.schemas import (
    LaborWorkerCreate,
    LaborWorkerSearch,
    LaborWorkerUpdate,
    LaborWorkHourCreate,
    LaborWorkHourSearch,
    LaborWorkHourUpdate,
)
from app.utils import CRUDRouter, ExcelConfig, ExcelDetail, SearchFieldConfig, require_buttons

labor_worker_crud = CRUDRouter(
    prefix="/labor_workers",
    controller=labor_worker_controller,
    create_schema=LaborWorkerCreate,
    excel=ExcelConfig(
        fields=("employee_no", "trade", "name", "remark"), update_key="id", details=(ExcelDetail(sheet_name="工票对应的工时_1", resource=lambda: labor_work_hour_crud, parent_field="worker_id"),)
    ),
    update_schema=LaborWorkerUpdate,
    list_schema=LaborWorkerSearch,
    route_key_prefix="labor_management.labor_workers",
    search_fields=SearchFieldConfig(contains_fields=["employee_no", "trade", "name", "remark"]),
    action_dependencies={
        "create": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_CREATE")],
        "update": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_EDIT")],
        "delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_DELETE")],
        "batch_delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_DELETE")],
        "import": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_IMPORT")],
        "import_template": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_IMPORT")],
        "export": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORKER_EXPORT")],
    },
    summary_prefix="劳务人员",
)

labor_work_hour_crud = CRUDRouter(
    prefix="/labor_work_hours",
    controller=labor_work_hour_controller,
    create_schema=LaborWorkHourCreate,
    excel=ExcelConfig(fields=("ticket_code", "work_hours", "order_no", "worker_id"), update_key="ticket_code"),
    update_schema=LaborWorkHourUpdate,
    list_schema=LaborWorkHourSearch,
    route_key_prefix="labor_management.labor_work_hours",
    search_fields=SearchFieldConfig(contains_fields=["ticket_code", "order_no"], exact_fields=["worker_id"]),
    action_dependencies={
        "create": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_CREATE")],
        "update": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_EDIT")],
        "delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_DELETE")],
        "batch_delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_DELETE")],
        "import": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_IMPORT")],
        "import_template": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_IMPORT")],
        "export": [require_buttons("B_LABOR_MANAGEMENT_LABOR_WORK_HOUR_EXPORT")],
    },
    summary_prefix="工票对应的工时",
)

router = APIRouter(tags=["labor_management"])


router.include_router(labor_worker_crud.router)
router.include_router(labor_work_hour_crud.router)
