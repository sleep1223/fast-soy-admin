"""
labor_management 管理接口 — CRUD。
"""

from datetime import date

from fastapi import APIRouter, File, Form, UploadFile

from app.business.labor_management.controllers import labor_project_controller, labor_receipt_controller, labor_work_hour_controller, labor_worker_controller
from app.business.labor_management.schemas import (
    LaborProjectCreate,
    LaborProjectSearch,
    LaborProjectUpdate,
    LaborReceiptCreate,
    LaborReceiptSearch,
    LaborReceiptUpdate,
    LaborWorkerCreate,
    LaborWorkerSearch,
    LaborWorkerUpdate,
    LaborWorkHourCreate,
    LaborWorkHourSearch,
    LaborWorkHourUpdate,
)
from app.business.labor_management.services import import_month_receipts
from app.utils import BizError, Code, CRUDRouter, ExcelConfig, ExcelDetail, SearchFieldConfig, Success, require_buttons

labor_receipt_crud = CRUDRouter(
    prefix="/labor_receipts",
    controller=labor_receipt_controller,
    create_schema=LaborReceiptCreate,
    update_schema=LaborReceiptUpdate,
    list_schema=LaborReceiptSearch,
    route_key_prefix="labor_management.labor_receipts",
    search_fields=SearchFieldConfig(contains_fields=["part_no"], range_fields=["receipt_month"]),
    action_dependencies={
        "create": [require_buttons("B_LABOR_MANAGEMENT_LABOR_RECEIPT_CREATE")],
        "update": [require_buttons("B_LABOR_MANAGEMENT_LABOR_RECEIPT_EDIT")],
        "delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_RECEIPT_DELETE")],
        "batch_delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_RECEIPT_DELETE")],
    },
    summary_prefix="月度接收工件明细",
)

labor_project_crud = CRUDRouter(
    prefix="/labor_projects",
    controller=labor_project_controller,
    create_schema=LaborProjectCreate,
    excel=ExcelConfig(fields=("part_no",), update_key="part_no"),
    update_schema=LaborProjectUpdate,
    list_schema=LaborProjectSearch,
    route_key_prefix="labor_management.labor_projects",
    search_fields=SearchFieldConfig(contains_fields=["part_no"]),
    action_dependencies={
        "create": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_CREATE")],
        "update": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_EDIT")],
        "delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_DELETE")],
        "batch_delete": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_DELETE")],
        "import": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_IMPORT")],
        "import_template": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_IMPORT")],
        "export": [require_buttons("B_LABOR_MANAGEMENT_LABOR_PROJECT_EXPORT")],
    },
    summary_prefix="劳务项目",
)

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
    search_fields=SearchFieldConfig(contains_fields=["ticket_code", "order_no"], exact_fields=["worker_id", "receipt_id"]),
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


@router.post("/labor_receipts/import-month", name="labor_management.labor_receipts.import_month", summary="导入月度接收工件", dependencies=[require_buttons("B_LABOR_MANAGEMENT_LABOR_RECEIPT_IMPORT")])
async def import_receipts(receipt_month: date = Form(...), file: UploadFile = File(...)) -> Success:
    """整表校验后，按月份和项目号幂等追加。"""
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise BizError(Code.REQUEST_VALIDATION, "Excel 文件不能超过 5MB")
    created, skipped = await import_month_receipts(content, receipt_month)
    return Success(data={"createdCount": created, "skippedCount": skipped})


router.include_router(labor_project_crud.router)
router.include_router(labor_receipt_crud.router)
router.include_router(labor_worker_crud.router)
router.include_router(labor_work_hour_crud.router)
