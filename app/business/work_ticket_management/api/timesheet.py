"""Work-time matrix, batch save and entry endpoints."""

from fastapi import APIRouter

from app.business.work_ticket_management import constants
from app.business.work_ticket_management.api.common import dump, excel_file, page
from app.business.work_ticket_management.schemas_workflow import (
    TimeBatchSaveIn,
    TimeEntryDeleteIn,
    TimeEntrySearchIn,
    TimeEntryUpdateIn,
    TimeMatrixIn,
)
from app.business.work_ticket_management.services import export, timesheet
from app.utils import BizError, Code, SqidPath, Success, SuccessExtra, require_buttons

router = APIRouter()


@router.post("/work_time_entries/search", summary="工时明细分页查询", name="work_ticket_management.work_time_entries.search")
async def search_entries(obj_in: TimeEntrySearchIn) -> SuccessExtra:
    total, records = await timesheet.list_entries(obj_in)
    return page(records, total, obj_in.current, obj_in.size)


@router.post("/work_time_entries/matrix", summary="工时矩阵数据", name="work_ticket_management.work_time_entries.matrix")
async def matrix(obj_in: TimeMatrixIn) -> Success:
    return Success(data=dump(await timesheet.matrix(obj_in)))


@router.post("/work_time_entries/batch-save", summary="批量保存工时", name="work_ticket_management.work_time_entries.batch_save", dependencies=[require_buttons(constants.B_TIME_EDIT)])
async def batch_save(obj_in: TimeBatchSaveIn) -> Success:
    return Success(data=dump(await timesheet.batch_save(obj_in)))


@router.patch("/work_time_entries/{item_id}", summary="修改工时", name="work_ticket_management.work_time_entries.update", dependencies=[require_buttons(constants.B_TIME_EDIT)])
async def update_entry(item_id: SqidPath, obj_in: TimeEntryUpdateIn) -> Success:
    return Success(data=dump(await timesheet.update_entry(item_id, obj_in)))


@router.delete("/work_time_entries/{item_id}", summary="删除工时", name="work_ticket_management.work_time_entries.delete", dependencies=[require_buttons(constants.B_TIME_DELETE)])
async def delete_entry(item_id: SqidPath, obj_in: TimeEntryDeleteIn) -> Success:
    await timesheet.delete_entry(item_id, obj_in)
    return Success(msg="删除成功")


@router.post("/work_time_entries/export", summary="导出月度工作簿中的工时", name="work_ticket_management.work_time_entries.export", dependencies=[require_buttons(constants.B_TIME_EXPORT)])
async def export_entries(obj_in: TimeEntrySearchIn) -> Success:
    if obj_in.work_month_id is None:
        raise BizError(code=Code.REQUEST_VALIDATION, msg="导出工时必须指定月度任务")
    content = await export.export_month_workbook(obj_in.work_month_id)
    return excel_file("work-time-entries.xlsx", content)
