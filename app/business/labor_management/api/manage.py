"""
labor_management 管理接口 — CRUD。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.business.labor_management.controllers import labor_project_controller, labor_work_hour_controller, labor_worker_controller
from app.business.labor_management.schemas import (
    LaborProjectCreate,
    LaborProjectSearch,
    LaborProjectUpdate,
    LaborWorkerCreate,
    LaborWorkerSearch,
    LaborWorkerUpdate,
    LaborWorkHourCreate,
    LaborWorkHourSearch,
    LaborWorkHourUpdate,
)
from app.business.labor_management.services import import_labor_projects
from app.utils import BizError, Code, CRUDRouter, ExcelConfig, ExcelDetail, ExcelImportOptions, SearchFieldConfig, Success, parse_excel, require_buttons

labor_project_crud = CRUDRouter(
    prefix="/labor_projects",
    controller=labor_project_controller,
    create_schema=LaborProjectCreate,
    excel=ExcelConfig(fields=("part_no",), update_key="part_no"),
    update_schema=LaborProjectUpdate,
    list_schema=LaborProjectSearch,
    route_key_prefix="labor_management.labor_projects",
    search_fields=SearchFieldConfig(contains_fields=["part_no"], exact_fields=["skip_painting"], range_fields=["imported_at"]),
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


@labor_project_crud.override("import")
async def import_projects(file: UploadFile = File(...), options: str | None = Form(None)) -> Success:
    """沿用项目 Excel 解析及字段映射，并在导入时记录首次导入时间。"""
    try:
        if not (file.filename or "").lower().endswith(".xlsx"):
            raise BizError(Code.REQUEST_VALIDATION, "只支持 .xlsx 文件")
        content = await file.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            raise BizError(Code.REQUEST_VALIDATION, "Excel 文件不能超过 5MB")
        try:
            selection = ExcelImportOptions.model_validate_json(options) if options is not None else ExcelImportOptions()
        except ValidationError as exc:
            raise BizError(Code.REQUEST_VALIDATION, "Excel 导入选项无效") from exc
        result = await run_in_threadpool(parse_excel, content, LaborProjectCreate, ExcelConfig(fields=("part_no",)), selection)
        if result.preview.errors:
            raise BizError(Code.REQUEST_VALIDATION, result.preview.errors[0])
        created, updated = await import_labor_projects(result.rows, datetime.now(timezone.utc))
        return Success(msg="导入成功", data={"importedCount": len(result.rows), "createdCount": created, "updatedCount": updated})
    finally:
        await file.close()


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
    excel=ExcelConfig(fields=("ticket_code", "work_hours", "order_no", "worker_id", "allocation_month"), update_key="ticket_code"),
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
router.include_router(labor_project_crud.router)


router.include_router(labor_worker_crud.router)
router.include_router(labor_work_hour_crud.router)
