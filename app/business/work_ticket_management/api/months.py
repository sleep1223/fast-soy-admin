"""Monthly task lifecycle endpoints."""

from fastapi import APIRouter

from app.business.work_ticket_management import constants
from app.business.work_ticket_management.api.common import dump, excel_file
from app.business.work_ticket_management.schemas_workflow import WorkMonthActionIn, WorkMonthCloseIn, WorkMonthOpenIn
from app.business.work_ticket_management.services import export, months
from app.business.work_ticket_management.services.common import actor_name
from app.utils import BizError, Code, SqidPath, Success, require_buttons

router = APIRouter()


@router.post("/work_months/open", summary="打开或创建月度任务", name="work_ticket_management.work_months.open", dependencies=[require_buttons(constants.B_MONTH_OPEN)])
async def open_month(obj_in: WorkMonthOpenIn) -> Success:
    return Success(data=dump(await months.open_month(obj_in, actor_name())))


@router.get("/work_months/{item_id}/summary", summary="月度任务汇总", name="work_ticket_management.work_months.summary")
async def month_summary(item_id: SqidPath) -> Success:
    return Success(data=dump(await months.summary(item_id)))


@router.get("/work_months/{item_id}/status-logs", summary="月度状态日志", name="work_ticket_management.work_months.status_logs")
async def month_status_logs(item_id: SqidPath) -> Success:
    return Success(data=dump(await months.list_status_logs(item_id)))


@router.post("/work_months/{item_id}/verify", summary="核对月度任务", name="work_ticket_management.work_months.verify", dependencies=[require_buttons(constants.B_MONTH_VERIFY)])
async def verify_month(item_id: SqidPath, obj_in: WorkMonthActionIn) -> Success:
    return Success(data=dump(await months.verify_month(item_id, obj_in.revision, obj_in.reason, actor_name())))


@router.post("/work_months/{item_id}/close", summary="关闭月度任务", name="work_ticket_management.work_months.close", dependencies=[require_buttons(constants.B_MONTH_CLOSE)])
async def close_month(item_id: SqidPath, obj_in: WorkMonthCloseIn) -> Success:
    return Success(data=dump(await months.close_month(item_id, obj_in, actor_name())))


@router.post("/work_months/{item_id}/reopen", summary="重新打开月度任务", name="work_ticket_management.work_months.reopen", dependencies=[require_buttons(constants.B_MONTH_REOPEN)])
async def reopen_month(item_id: SqidPath, obj_in: WorkMonthActionIn) -> Success:
    if obj_in.reason is None:
        raise BizError(code=Code.REQUEST_VALIDATION, msg="重新打开必须填写原因")
    return Success(data=dump(await months.reopen_month(item_id, obj_in.revision, obj_in.reason, actor_name())))


@router.post("/work_months/{item_id}/export", summary="导出月度工作簿", name="work_ticket_management.work_months.export", dependencies=[require_buttons(constants.B_MONTH_EXPORT)])
async def export_month(item_id: SqidPath) -> Success:
    summary = await months.summary(item_id)
    content = await export.export_month_workbook(item_id)
    return excel_file(f"{summary.year_month}-work-tickets.xlsx", content)
