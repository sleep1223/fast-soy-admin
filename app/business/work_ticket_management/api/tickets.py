"""Work ticket aggregate endpoints."""

from fastapi import APIRouter

from app.business.work_ticket_management import constants
from app.business.work_ticket_management.api.common import dump, excel_file, page
from app.business.work_ticket_management.schemas_workflow import (
    CodeConfirmIn,
    CodeLookupIn,
    CodePasteIn,
    CodePreviewIn,
    OcrCandidateIn,
    TicketAssignIn,
    TicketBatchAssignIn,
    TicketCreateIn,
    TicketReconcileIn,
    TicketSearchIn,
    TicketUnassignIn,
    TicketUpdateIn,
    TicketVoidIn,
)
from app.business.work_ticket_management.services import export, tickets
from app.utils import BizError, Code, SqidPath, Success, SuccessExtra, require_buttons

router = APIRouter()


@router.post("/work_tickets/search", summary="工票分页查询", name="work_ticket_management.work_tickets.search")
async def search(obj_in: TicketSearchIn) -> SuccessExtra:
    total, records = await tickets.list_tickets(obj_in)
    return page(records, total, obj_in.current, obj_in.size)


@router.get("/work_tickets/{item_id}", summary="工票详情", name="work_ticket_management.work_tickets.detail")
async def detail(item_id: SqidPath) -> Success:
    return Success(data=dump(await tickets.detail(item_id)))


@router.post("/work_tickets", summary="创建工票", name="work_ticket_management.work_tickets.create", dependencies=[require_buttons(constants.B_TICKET_CREATE)])
async def create(obj_in: TicketCreateIn) -> Success:
    return Success(data=dump(await tickets.create_ticket(obj_in)))


@router.patch("/work_tickets/{item_id}", summary="更新工票", name="work_ticket_management.work_tickets.update", dependencies=[require_buttons(constants.B_TICKET_EDIT)])
async def update(item_id: SqidPath, obj_in: TicketUpdateIn) -> Success:
    return Success(data=dump(await tickets.update_ticket(item_id, obj_in)))


@router.post("/work_tickets/{item_id}/void", summary="作废工票", name="work_ticket_management.work_tickets.void", dependencies=[require_buttons(constants.B_TICKET_VOID)])
async def void(item_id: SqidPath, obj_in: TicketVoidIn) -> Success:
    return Success(data=dump(await tickets.void_ticket(item_id, obj_in)))


@router.post("/work_tickets/{item_id}/assign", summary="分配工票人员", name="work_ticket_management.work_tickets.assign", dependencies=[require_buttons(constants.B_TICKET_ASSIGN)])
async def assign(item_id: SqidPath, obj_in: TicketAssignIn) -> Success:
    return Success(data=dump(await tickets.assign_workers(item_id, obj_in)))


@router.post("/work_tickets/{item_id}/unassign", summary="移除工票人员", name="work_ticket_management.work_tickets.unassign", dependencies=[require_buttons(constants.B_TICKET_ASSIGN)])
async def unassign(item_id: SqidPath, obj_in: TicketUnassignIn) -> Success:
    return Success(data=dump(await tickets.remove_assignment(item_id, obj_in.worker_id, obj_in.revision)))


@router.post("/work_tickets/batch-assign", summary="批量分配工票人员", name="work_ticket_management.work_tickets.batch_assign", dependencies=[require_buttons(constants.B_TICKET_ASSIGN)])
async def batch_assign(obj_in: TicketBatchAssignIn) -> Success:
    return Success(data=await tickets.batch_assign(obj_in))


@router.post("/work_tickets/{item_id}/reconcile", summary="标记工票核对", name="work_ticket_management.work_tickets.reconcile", dependencies=[require_buttons(constants.B_TICKET_RECONCILE)])
async def reconcile(item_id: SqidPath, obj_in: TicketReconcileIn) -> Success:
    return Success(data=dump(await tickets.reconcile_ticket(item_id, obj_in)))


@router.post("/work_tickets/code-preview", summary="预览工票码", name="work_ticket_management.work_tickets.code_preview", dependencies=[require_buttons(constants.B_TICKET_CODE)])
async def code_preview(obj_in: CodePreviewIn) -> Success:
    return Success(data=dump(await tickets.preview_codes(obj_in)))


@router.post("/work_tickets/code-confirm", summary="确认并创建工票码", name="work_ticket_management.work_tickets.code_confirm", dependencies=[require_buttons(constants.B_TICKET_CODE)])
async def code_confirm(obj_in: CodeConfirmIn) -> Success:
    return Success(data=dump(await tickets.confirm_codes(obj_in)))


@router.post("/work_tickets/codes/import", summary="批量粘贴工票码", name="work_ticket_management.work_tickets.codes_import", dependencies=[require_buttons(constants.B_TICKET_CODE)])
async def paste_codes(obj_in: CodePasteIn) -> Success:
    return Success(data=dump(await tickets.paste_codes(obj_in)))


@router.post("/work_tickets/code-lookup", summary="按工票码查询", name="work_ticket_management.work_tickets.code_lookup")
async def code_lookup(obj_in: CodeLookupIn) -> Success:
    return Success(data=dump(await tickets.code_lookup(obj_in)))


@router.post("/work_tickets/ocr-candidates", summary="OCR 文本解析工票码", name="work_ticket_management.work_tickets.ocr_candidates", dependencies=[require_buttons(constants.B_TICKET_OCR)])
async def ocr_candidates(obj_in: OcrCandidateIn) -> Success:
    return Success(data=dump(await tickets.ocr_candidates(obj_in)))


@router.post("/work_tickets/export", summary="导出月度工票工作簿", name="work_ticket_management.work_tickets.export", dependencies=[require_buttons(constants.B_TICKET_EXPORT)])
async def export_tickets(obj_in: TicketSearchIn) -> Success:
    if obj_in.work_month_id is None:
        raise BizError(code=Code.REQUEST_VALIDATION, msg="导出工票必须指定月度任务")
    content = await export.export_month_workbook(obj_in.work_month_id)
    return excel_file("work-tickets.xlsx", content)
