"""Computed monthly reconciliation endpoints."""

from fastapi import APIRouter

from app.business.work_ticket_management.api.common import dump, page
from app.business.work_ticket_management.schemas_workflow import ReconcileSearchIn
from app.business.work_ticket_management.services import reconciliation
from app.utils import SqidPath, Success, SuccessExtra

router = APIRouter()


@router.get("/work_months/{item_id}/reconciliation/summary", summary="月度核对汇总", name="work_ticket_management.work_months.reconciliation_summary")
async def summary(item_id: SqidPath) -> Success:
    return Success(data=dump(await reconciliation.summary(item_id)))


@router.post("/work_months/{item_id}/reconciliation/search", summary="月度核对分类分页", name="work_ticket_management.work_months.reconciliation_search")
async def search(item_id: SqidPath, obj_in: ReconcileSearchIn) -> SuccessExtra:
    total, items = await reconciliation.search(item_id, obj_in)
    return page(items, total, obj_in.current, obj_in.size)
