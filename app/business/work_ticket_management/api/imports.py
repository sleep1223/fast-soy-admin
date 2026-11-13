"""Monthly import preview/commit, row corrections and batch voiding."""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import ValidationError

from app.business.work_ticket_management import constants
from app.business.work_ticket_management.api.common import dump, page
from app.business.work_ticket_management.models import ImportSourceType
from app.business.work_ticket_management.schemas_workflow import (
    ImportBatchVoidIn,
    ImportRowBatchMatchIn,
    ImportRowIgnoreIn,
    ImportRowMatchIn,
    ImportRowSearchIn,
    ImportRowUpdateIn,
    ManualImportIn,
)
from app.business.work_ticket_management.services import imports
from app.core.excel import ExcelImportOptions
from app.utils import BizError, Code, SqidPath, Success, SuccessExtra, decode_id, require_buttons

router = APIRouter()
MAX_IMPORT_BYTES = 5 * 1024 * 1024


def _parse_options(raw: str | None) -> ExcelImportOptions | None:
    if raw is None or not raw.strip():
        return None
    try:
        return ExcelImportOptions.model_validate_json(raw)
    except ValidationError as exc:
        raise BizError(code=Code.REQUEST_VALIDATION, msg="Excel 导入参数无效") from exc


async def _read_file(file: UploadFile) -> bytes:
    try:
        content = await file.read(MAX_IMPORT_BYTES + 1)
        if len(content) > MAX_IMPORT_BYTES:
            raise BizError(code=Code.REQUEST_VALIDATION, msg="Excel 文件不能超过 5MB")
        if not (file.filename or "").lower().endswith(".xlsx"):
            raise BizError(code=Code.REQUEST_VALIDATION, msg="只支持 .xlsx 文件")
        return content
    finally:
        await file.close()


@router.post(
    "/monthly_import_batches/preview",
    summary="预览月度清单",
    name="work_ticket_management.monthly_import_batches.preview",
    dependencies=[require_buttons(constants.B_IMPORT_PLAN, constants.B_IMPORT_ACTUAL)],
)
async def preview_import(
    file: Annotated[UploadFile, File(description="Excel 文件")],
    work_month_id: Annotated[str, Form()],
    source_type: Annotated[ImportSourceType, Form()],
    options: Annotated[str | None, Form()] = None,
) -> Success:
    content = await _read_file(file)
    result = await imports.preview_import(decode_id(work_month_id), source_type, content, _parse_options(options))
    return Success(data=dump(result))


@router.post(
    "/monthly_import_batches/import",
    summary="提交月度清单",
    name="work_ticket_management.monthly_import_batches.import",
    dependencies=[require_buttons(constants.B_IMPORT_PLAN, constants.B_IMPORT_ACTUAL)],
)
async def commit_import(
    file: Annotated[UploadFile, File(description="Excel 文件")],
    work_month_id: Annotated[str, Form()],
    source_type: Annotated[ImportSourceType, Form()],
    source_name: Annotated[str | None, Form()] = None,
    options: Annotated[str | None, Form()] = None,
) -> Success:
    content = await _read_file(file)
    result = await imports.commit_import(decode_id(work_month_id), source_type, content, _parse_options(options), source_name or file.filename)
    return Success(data=dump(result))


@router.post("/monthly_import_batches/manual", summary="手工补录导入行", name="work_ticket_management.monthly_import_batches.manual", dependencies=[require_buttons(constants.B_IMPORT_MANUAL)])
async def manual_import(obj_in: ManualImportIn) -> Success:
    return Success(data=dump(await imports.manual_import(obj_in)))


@router.post("/monthly_import_batches/{item_id}/void", summary="作废导入批次", name="work_ticket_management.monthly_import_batches.void", dependencies=[require_buttons(constants.B_IMPORT_VOID)])
async def void_batch(item_id: SqidPath, obj_in: ImportBatchVoidIn) -> Success:
    await imports.void_batch(item_id, obj_in)
    return Success(msg="批次已作废")


@router.post("/monthly_import_rows/search", summary="导入行分页查询", name="work_ticket_management.monthly_import_rows.search")
async def search_rows(obj_in: ImportRowSearchIn) -> SuccessExtra:
    total, rows = await imports.list_rows(obj_in)
    return page(rows, total, obj_in.current, obj_in.size)


@router.patch("/monthly_import_rows/{item_id}", summary="修改导入行", name="work_ticket_management.monthly_import_rows.update", dependencies=[require_buttons(constants.B_IMPORT_ROW_EDIT)])
async def update_row(item_id: SqidPath, obj_in: ImportRowUpdateIn) -> Success:
    return Success(data=dump(await imports.update_row(item_id, obj_in)))


@router.post("/monthly_import_rows/{item_id}/match", summary="确认导入行订单", name="work_ticket_management.monthly_import_rows.match", dependencies=[require_buttons(constants.B_IMPORT_ROW_MATCH)])
async def match_row(item_id: SqidPath, obj_in: ImportRowMatchIn) -> Success:
    return Success(data=dump(await imports.match_row(item_id, obj_in)))


@router.post("/monthly_import_rows/{item_id}/ignore", summary="忽略导入行", name="work_ticket_management.monthly_import_rows.ignore", dependencies=[require_buttons(constants.B_IMPORT_ROW_IGNORE)])
async def ignore_row(item_id: SqidPath, obj_in: ImportRowIgnoreIn) -> Success:
    return Success(data=dump(await imports.ignore_row(item_id, obj_in)))


@router.post(
    "/monthly_import_rows/batch-match",
    summary="批量重新匹配导入行",
    name="work_ticket_management.monthly_import_rows.batch_match",
    dependencies=[require_buttons(constants.B_IMPORT_ROW_MATCH)],
)
async def batch_match(obj_in: ImportRowBatchMatchIn) -> Success:
    return Success(data=await imports.batch_match(obj_in))
