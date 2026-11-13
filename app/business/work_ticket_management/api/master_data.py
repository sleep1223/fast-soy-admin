"""Options and order candidate endpoints for the workbench."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.business.work_ticket_management.schemas_workflow import OrderCandidateQuery
from app.business.work_ticket_management.services import master_data
from app.utils import SqidId, Success

router = APIRouter()


@router.get("/options/production_units", summary="可选生产单位", name="work_ticket_management.options.production_units")
async def production_unit_options(enabled_only: bool = True) -> Success:
    return Success(data=[item.model_dump(mode="json", by_alias=True) for item in await master_data.unit_options(enabled_only=enabled_only)])


@router.get("/options/workers", summary="可选生产人员", name="work_ticket_management.options.workers")
async def worker_options(
    production_unit_id: Annotated[SqidId | None, Query()] = None,
    include_disabled: bool = False,
) -> Success:
    return Success(data=[item.model_dump(mode="json", by_alias=True) for item in await master_data.worker_options(production_unit_id, include_disabled=include_disabled)])


@router.post("/orders/candidates", summary="按项目号查询订单候选", name="work_ticket_management.orders.candidates")
async def order_candidates(obj_in: OrderCandidateQuery) -> Success:
    data = await master_data.order_candidates(obj_in)
    return Success(data=[item.model_dump(mode="json", by_alias=True) for item in data])
