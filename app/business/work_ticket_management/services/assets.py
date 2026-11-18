"""Import order assets, register external tickets and allocate hours."""

from __future__ import annotations

import asyncio
import unicodedata
from decimal import Decimal
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import IntegrityError
from tortoise.functions import Count, Sum
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import TicketCodeSource, WorkAssetAllocation, WorkAssetTicket, Worker, WorkProject, WorkProjectOrder
from app.business.work_ticket_management.rules import normalize_ticket_code
from app.business.work_ticket_management.schemas_assets import (
    WorkAssetAllocationCreate,
    WorkAssetAllocationOut,
    WorkAssetAllocationUpdate,
    WorkAssetReportRow,
    WorkAssetReportSearch,
    WorkAssetTicketCreate,
    WorkAssetTicketOut,
    WorkProjectImportOut,
    WorkProjectImportRow,
    WorkProjectOrderOut,
    WorkProjectOut,
    WorkProjectSearch,
)
from app.business.work_ticket_management.services.common import chunked, sqid
from app.business.work_ticket_management.services.order_access import order_model
from app.utils import BizError, Code, ExcelColumn, ExcelConfig, ExcelImportOptions, ExcelImportResult, PageQueryBase, get_db_conn, parse_excel, radar_log

PROJECT_EXCEL = ExcelConfig(fields=("part_no",), columns={"part_no": ExcelColumn(title="项目号", aliases=("件号", "part_no", "partNo"))})


async def parse_project_excel(content: bytes, options: ExcelImportOptions | None) -> ExcelImportResult:
    return await asyncio.to_thread(parse_excel, content, WorkProjectImportRow, PROJECT_EXCEL, options)


async def import_projects(owner_id: int, parsed: ExcelImportResult) -> WorkProjectImportOut:
    if parsed.preview.errors:
        raise BizError(Code.REQUEST_VALIDATION, "；".join(parsed.preview.errors))
    part_numbers = sorted({row.part_no for _, row in parsed.rows if isinstance(row, WorkProjectImportRow)})
    new_projects = new_orders = unmatched = 0
    async with in_transaction(get_db_conn(WorkProject)) as db:
        for batch in chunked(part_numbers):
            orders = await order_model().filter(part_no__in=batch).using_db(db).order_by("id").values("id", "part_no", "order_no", "name")
            by_part: dict[str, list[dict[str, Any]]] = {part_no: [] for part_no in batch}
            for order in orders:
                if order["part_no"] in by_part:
                    by_part[order["part_no"]].append(order)
            for part_no, matches in by_part.items():
                project, created = await WorkProject.get_or_create(owner_id=owner_id, part_no=part_no, using_db=db, defaults={"created_by": str(owner_id)})
                new_projects += created
                # Serialize repeat imports for a project and preserve existing asset snapshots.
                await WorkProject.filter(id=project.id).using_db(db).select_for_update().get()
                existing = await WorkProjectOrder.filter(project_id=project.id).using_db(db).values("order_id", "order_no")
                source_ids = {row["order_id"] for row in existing}
                order_numbers = {row["order_no"] for row in existing}
                additions = [
                    WorkProjectOrder(project_id=project.id, order_id=row["id"], order_no=row["order_no"], name=row["name"], created_by=str(owner_id))
                    for row in matches
                    if row["id"] not in source_ids and row["order_no"] not in order_numbers
                ]
                if additions:
                    await WorkProjectOrder.bulk_create(additions, using_db=db, batch_size=200)
                new_orders += len(additions)
                unmatched += not (existing or matches)
    radar_log("导入项目资产", data={"projectCount": new_projects, "orderCount": new_orders, "unmatchedCount": unmatched})
    return WorkProjectImportOut(imported_count=len(part_numbers), created_count=new_projects, matched_order_count=new_orders, unmatched_project_count=unmatched)


async def list_projects(owner_id: int, query: WorkProjectSearch) -> tuple[int, list[WorkProjectOut]]:
    projects = WorkProject.filter(owner_id=owner_id)
    if query.part_no and (keyword := query.part_no.strip()):
        projects = projects.filter(part_no__icontains=keyword)
    total = await projects.count()
    rows = await projects.annotate(order_count=Count("asset_orders")).order_by("part_no", "id").offset((query.current - 1) * query.size).limit(query.size).values("id", "part_no", "order_count")
    return total, [WorkProjectOut(id=sqid(row["id"]), part_no=row["part_no"], order_count=row["order_count"]) for row in rows]


async def list_orders(owner_id: int, project_id: int, query: PageQueryBase) -> tuple[int, list[WorkProjectOrderOut]]:
    if not await WorkProject.filter(id=project_id, owner_id=owner_id).exists():
        raise BizError(Code.NOT_FOUND, "项目不存在")
    orders = WorkProjectOrder.filter(project_id=project_id)
    total = await orders.count()
    rows = (
        await orders
        .annotate(ticket_count=Count("asset_tickets"))
        .order_by("order_no", "id")
        .offset((query.current - 1) * query.size)
        .limit(query.size)
        .values("id", "order_no", "name", "ticket_count")
    )
    return total, [WorkProjectOrderOut(id=sqid(row["id"]), order_no=row["order_no"], name=row["name"], ticket_count=row["ticket_count"]) for row in rows]


async def list_tickets(owner_id: int, order_id: int) -> list[WorkAssetTicketOut]:
    if not await WorkProjectOrder.filter(id=order_id, project__owner_id=owner_id).exists():
        raise BizError(Code.WORK_ORDER_NOT_FOUND, "项目订单不存在")
    tickets = await WorkAssetTicket.filter(project_order_id=order_id).order_by("id").prefetch_related("allocations__worker")
    result: list[WorkAssetTicketOut] = []
    for ticket in tickets:
        allocations = [
            WorkAssetAllocationOut(
                id=sqid(row.id),
                worker_id=sqid(row.worker_id),
                worker_name=row.worker.name,
                assigned_on=row.assigned_on,
                hours=row.hours,
            )
            for row in sorted(ticket.allocations, key=lambda item: (item.assigned_on, item.id), reverse=True)
        ]
        result.append(
            WorkAssetTicketOut(
                id=sqid(ticket.id),
                ticket_code=ticket.ticket_code,
                code_source=ticket.code_source.value,
                total_hours=ticket.total_hours,
                assigned_hours=sum((row.hours or Decimal(0) for row in allocations), Decimal(0)),
                allocations=allocations,
            )
        )
    return result


async def lock_ticket(owner_id: int, ticket_id: int, db: BaseDBAsyncClient) -> WorkAssetTicket:
    owned = await WorkAssetTicket.filter(id=ticket_id, project_order__project__owner_id=owner_id).using_db(db).exists()
    if not owned:
        raise BizError(Code.WORK_TICKET_NOT_FOUND, "工票不存在")
    return await WorkAssetTicket.filter(id=ticket_id).using_db(db).select_for_update().get()


def ticket_codes(raw: str) -> tuple[str, str]:
    normalized = unicodedata.normalize("NFKC", raw).strip()
    display, key = normalize_ticket_code(normalized)
    if not display or not key or len(normalized) > 100 or len(normalized.upper()) > 100 or any(ord(char) < 32 for char in normalized):
        raise BizError(Code.WORK_TICKET_CODE_INVALID, "请输入 100 字符以内的工票码")
    return display, key


async def save_ticket(owner_id: int, item_id: int, payload: WorkAssetTicketCreate, *, editing: bool = False) -> int:
    display, key = ticket_codes(payload.ticket_code)
    try:
        async with in_transaction(get_db_conn(WorkAssetTicket)) as db:
            if editing:
                ticket = await lock_ticket(owner_id, item_id, db)
                await validate_hours(ticket.id, payload.total_hours, None, db)
                ticket.ticket_code = display
                ticket.ticket_code_key = key
                ticket.code_source = TicketCodeSource(payload.code_source)
                ticket.total_hours = payload.total_hours
                ticket.updated_by = str(owner_id)
                await ticket.save(using_db=db, update_fields=["ticket_code", "ticket_code_key", "code_source", "total_hours", "updated_by", "updated_at"])
            else:
                if not await WorkProjectOrder.filter(id=item_id, project__owner_id=owner_id).using_db(db).exists():
                    raise BizError(Code.WORK_ORDER_NOT_FOUND, "项目订单不存在")
                ticket = await WorkAssetTicket.create(
                    project_order_id=item_id,
                    ticket_code=display,
                    ticket_code_key=key,
                    code_source=TicketCodeSource(payload.code_source),
                    total_hours=payload.total_hours,
                    created_by=str(owner_id),
                    using_db=db,
                )
    except IntegrityError as exc:
        raise BizError(Code.WORK_TICKET_CODE_CONFLICT, "该订单已登记相同工票码") from exc
    radar_log("更新资产工票" if editing else "登记资产工票", data={"ticketId": ticket.id})
    return ticket.id


async def validate_hours(
    ticket_id: int,
    total: Decimal | None,
    hours: Decimal | None,
    db: BaseDBAsyncClient,
    *,
    exclude_id: int | None = None,
) -> None:
    if total is None:
        return
    existing = WorkAssetAllocation.filter(ticket_id=ticket_id).using_db(db)
    if exclude_id is not None:
        existing = existing.exclude(id=exclude_id)
    values = await existing.values("hours")
    if sum((row["hours"] or Decimal(0) for row in values), hours or Decimal(0)) > total:
        raise BizError(Code.WORK_TIME_INVALID, "分配工时合计不能超过工票总工时")


async def require_enabled_worker(worker_id: int, db: BaseDBAsyncClient) -> None:
    if not await Worker.filter(id=worker_id, enabled=True).using_db(db).select_for_update().first():
        raise BizError(Code.WORK_TICKET_WORKER_DISABLED, "人员不存在或已停用")


async def save_allocation(
    owner_id: int,
    ticket_id: int,
    payload: WorkAssetAllocationCreate | WorkAssetAllocationUpdate,
    allocation_id: int | None = None,
) -> int:
    try:
        async with in_transaction(get_db_conn(WorkAssetAllocation)) as db:
            ticket = await lock_ticket(owner_id, ticket_id, db)
            await validate_hours(ticket.id, ticket.total_hours, payload.hours, db, exclude_id=allocation_id)
            if isinstance(payload, WorkAssetAllocationCreate):
                await require_enabled_worker(payload.worker_id, db)
                allocation = await WorkAssetAllocation.create(
                    ticket_id=ticket.id,
                    worker_id=payload.worker_id,
                    assigned_on=payload.assigned_on,
                    hours=payload.hours,
                    created_by=str(owner_id),
                    using_db=db,
                )
            else:
                allocation = await WorkAssetAllocation.filter(ticket_id=ticket.id, id=allocation_id).using_db(db).first()
                if allocation is None:
                    raise BizError(Code.WORK_TICKET_ASSIGNMENT_NOT_FOUND, "人员分配不存在")
                if allocation.worker_id != payload.worker_id:
                    await require_enabled_worker(payload.worker_id, db)
                    allocation.worker_id = payload.worker_id
                allocation.assigned_on = payload.assigned_on
                allocation.hours = payload.hours
                allocation.updated_by = str(owner_id)
                await allocation.save(using_db=db, update_fields=["worker_id", "assigned_on", "hours", "updated_by", "updated_at"])
    except IntegrityError as exc:
        raise BizError(Code.WORK_TIME_INVALID, "该人员在同一天已有分配记录，请修改原记录") from exc
    radar_log("保存工票人员分配", data={"ticketId": ticket_id, "allocationId": allocation.id})
    return allocation.id


async def report(owner_id: int, query: WorkAssetReportSearch) -> list[WorkAssetReportRow]:
    allocations = WorkAssetAllocation.filter(
        ticket__project_order__project__owner_id=owner_id,
        assigned_on__gte=query.start_date,
        assigned_on__lte=query.end_date,
    )
    if query.production_unit_id is not None:
        allocations = allocations.filter(worker__production_unit_id=query.production_unit_id)
    rows = (
        await allocations
        .annotate(allocation_count=Count("id"), allocated_hours=Sum("hours"))
        .group_by(
            "worker_id",
            "worker__name",
            "worker__production_unit__name",
        )
        .order_by("worker__name", "worker_id")
        .values("worker_id", "allocation_count", "allocated_hours", worker_name="worker__name", production_unit_name="worker__production_unit__name")
    )
    return [
        WorkAssetReportRow(
            worker_id=sqid(row["worker_id"]),
            worker_name=row["worker_name"],
            production_unit_name=row["production_unit_name"],
            allocation_count=row["allocation_count"],
            hours=Decimal(str(row["allocated_hours"] or 0)).quantize(Decimal("0.01")),
        )
        for row in rows
    ]
