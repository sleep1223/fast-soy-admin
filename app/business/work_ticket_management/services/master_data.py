"""Production units, workers and order-to-unit mapping operations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import (
    OrderUnitMapping,
    ProductionUnit,
    Worker,
    WorkMonth,
    WorkTicketAssignment,
)
from app.business.work_ticket_management.schemas_workflow import MappingRowOut, MappingSearchIn, OrderCandidateOut, OrderCandidateQuery, UnitOption, WorkerOption
from app.business.work_ticket_management.services.common import sqid
from app.business.work_ticket_management.services.matching import Candidate, candidates
from app.business.work_ticket_management.services.order_access import get_order
from app.utils import BizError, Code, get_db_conn


async def unit_options(*, enabled_only: bool = True) -> list[UnitOption]:
    query = ProductionUnit.all()
    if enabled_only:
        query = query.filter(enabled=True)
    units = await query.order_by("name", "id")
    return [UnitOption(id=sqid(unit.id), code=unit.code, name=unit.name) for unit in units]


async def worker_options(production_unit_id: int | None, *, include_disabled: bool = False) -> list[WorkerOption]:
    query = Worker.all()
    if production_unit_id is not None:
        query = query.filter(production_unit_id=production_unit_id)
    if not include_disabled:
        query = query.filter(enabled=True)
    workers = await query.order_by("name", "id")
    return [
        WorkerOption(
            id=sqid(worker.id),
            worker_no=worker.worker_no,
            name=worker.name,
            production_unit_id=sqid(worker.production_unit_id),
            enabled=worker.enabled,
        )
        for worker in workers
    ]  # type: ignore[arg-type]


async def get_month_unit(month_id: int, db: BaseDBAsyncClient | None = None) -> tuple[WorkMonth, ProductionUnit]:
    query = WorkMonth.filter(id=month_id)
    if db is not None:
        query = query.using_db(db)
    month = await query.select_related("production_unit").first()
    if month is None:
        raise BizError(code=Code.WORK_MONTH_NOT_FOUND, msg="月度任务不存在")
    unit = month.production_unit
    if unit is None:
        raise BizError(code=Code.WORK_MONTH_NOT_FOUND, msg="月度任务的生产单位不存在")
    return month, unit


def candidate_out(candidate: Candidate) -> OrderCandidateOut:
    order = candidate.order
    return OrderCandidateOut(
        id=sqid(order.id),
        order_no=str(getattr(order, "order_no", "") or ""),
        part_no=str(getattr(order, "part_no", "") or ""),
        name=str(getattr(order, "name", "") or ""),
        net_weight=Decimal(getattr(order, "net_weight", 0) or 0),
        gross_weight=Decimal(getattr(order, "gross_weight", 0)) if getattr(order, "gross_weight", None) is not None else None,
        process_route=getattr(order, "process_route", None),
        quantity=getattr(order, "quantity", None),
        received_quantity=getattr(order, "received_quantity", None),
        mapping_status=candidate.mapping_status,
        mapped_units=list(candidate.mapped_units),
    )


async def order_candidates(query: OrderCandidateQuery, db: BaseDBAsyncClient | None = None) -> list[OrderCandidateOut]:
    if db is None:
        async with in_transaction(get_db_conn(WorkMonth)) as connection:
            return await order_candidates(query, connection)
    _, unit = await get_month_unit(query.work_month_id, db)
    found = await candidates(
        query.part_no,
        unit.id,
        include_other_units=query.include_other_units,
        include_partial=query.include_partial,
        limit=query.limit,
        db=db,
    )
    return [candidate_out(candidate) for candidate in found]


async def all_mappings(order_id: int, db: BaseDBAsyncClient) -> dict[int, str]:
    mappings = await OrderUnitMapping.filter(order_id=order_id).using_db(db).prefetch_related("production_unit")
    return {mapping.production_unit_id: mapping.production_unit.name for mapping in mappings if mapping.production_unit is not None}


async def search_mappings(search: MappingSearchIn) -> tuple[int, list[MappingRowOut]]:
    query = OrderUnitMapping.all()
    if search.production_unit_id is not None:
        query = query.filter(production_unit_id=search.production_unit_id)
    if search.keyword:
        keyword = search.keyword.strip()
        if keyword:
            query = query.filter(Q(order__order_no__icontains=keyword) | Q(order__part_no__icontains=keyword) | Q(order__name__icontains=keyword) | Q(production_unit__name__icontains=keyword))
    total = await query.count()
    mappings = await query.prefetch_related("order", "production_unit").order_by("-id").offset((search.current - 1) * search.size).limit(search.size)
    rows: list[MappingRowOut] = []
    for mapping in mappings:
        order = mapping.order
        unit = mapping.production_unit
        if order is None or unit is None:
            continue
        rows.append(
            MappingRowOut(
                id=sqid(mapping.id),
                order_id=sqid(mapping.order_id),
                order_no=getattr(order, "order_no", None),
                part_no=getattr(order, "part_no", None),
                name=getattr(order, "name", None),
                production_unit_id=sqid(mapping.production_unit_id),
                production_unit_name=unit.name,
                remark=mapping.remark,
                created_at=mapping.created_at,
            )
        )
    return total, rows


async def confirm_mapping(order_id: int, production_unit_id: int, db: BaseDBAsyncClient, actor: str, remark: str | None = None) -> OrderUnitMapping:
    order = await get_order(order_id, db)
    if order is None:
        raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="订单不存在")
    unit = await ProductionUnit.filter(id=production_unit_id).using_db(db).first()
    if unit is None:
        raise BizError(code=Code.WORK_UNIT_IN_USE, msg="生产单位不存在")
    mapping, _ = await OrderUnitMapping.get_or_create(
        order_id=order_id,
        production_unit_id=production_unit_id,
        defaults={"remark": remark, "created_by": actor, "updated_by": actor},
        using_db=db,
    )
    return mapping


async def ensure_order_mapping(order_id: int, production_unit_id: int, db: BaseDBAsyncClient, actor: str, *, allow_add_mapping: bool) -> None:
    mapping = await OrderUnitMapping.filter(order_id=order_id, production_unit_id=production_unit_id).using_db(db).exists()
    if mapping:
        return
    if not allow_add_mapping:
        raise BizError(code=Code.WORK_TICKET_ORDER_UNIT_MISMATCH, msg="订单尚未关联当前生产单位，请先确认单位关联")
    await confirm_mapping(order_id, production_unit_id, db, actor, remark="工票匹配自动确认")


async def delete_worker(worker_id: int, db: BaseDBAsyncClient) -> None:
    worker = await Worker.filter(id=worker_id).using_db(db).first()
    if worker is None:
        raise BizError(code=Code.WORK_WORKER_NOT_FOUND, msg="人员不存在")
    if await WorkTicketAssignment.filter(worker_id=worker_id).using_db(db).exists():
        raise BizError(code=Code.WORK_WORKER_HAS_HISTORY, msg=f"人员 {worker.name} 已有工票分配记录，请停用而非删除")
    await worker.delete(using_db=db)


async def delete_workers(worker_ids: list[int], db: BaseDBAsyncClient) -> None:
    for worker_id in sorted(set(worker_ids)):
        await delete_worker(worker_id, db)


async def delete_production_unit(unit_id: int, db: BaseDBAsyncClient) -> None:
    unit = await ProductionUnit.filter(id=unit_id).using_db(db).first()
    if unit is None:
        raise BizError(code=Code.WORK_UNIT_IN_USE, msg="生产单位不存在")
    if await WorkMonth.filter(production_unit_id=unit_id).using_db(db).exists() or await OrderUnitMapping.filter(production_unit_id=unit_id).using_db(db).exists():
        raise BizError(code=Code.WORK_UNIT_IN_USE, msg=f"生产单位 {unit.name} 已有关联记录，请停用而非删除")
    await unit.delete(using_db=db)


async def delete_production_units(unit_ids: list[int], db: BaseDBAsyncClient) -> None:
    for unit_id in sorted(set(unit_ids)):
        await delete_production_unit(unit_id, db)


async def delete_mapping(mapping_id: int, db: BaseDBAsyncClient) -> None:
    mapping = await OrderUnitMapping.filter(id=mapping_id).using_db(db).first()
    if mapping is None:
        raise BizError(code=Code.NOT_FOUND, msg="订单单位关联不存在")
    await mapping.delete(using_db=db)


async def create_mapping_from_payload(order_id: int, production_unit_id: int, remark: str | None, actor: str) -> dict[str, Any]:
    async with in_transaction(get_db_conn(OrderUnitMapping)) as db:
        mapping = await confirm_mapping(order_id, production_unit_id, db, actor, remark)
        return await mapping.to_dict()


async def remove_worker(worker_id: int) -> None:
    async with in_transaction(get_db_conn(Worker)) as db:
        await delete_worker(worker_id, db)


async def remove_workers(worker_ids: list[int]) -> None:
    async with in_transaction(get_db_conn(Worker)) as db:
        await delete_workers(worker_ids, db)


async def remove_production_unit(unit_id: int) -> None:
    async with in_transaction(get_db_conn(ProductionUnit)) as db:
        await delete_production_unit(unit_id, db)


async def remove_production_units(unit_ids: list[int]) -> None:
    async with in_transaction(get_db_conn(ProductionUnit)) as db:
        await delete_production_units(unit_ids, db)
