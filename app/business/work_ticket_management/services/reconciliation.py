"""Computed monthly discrepancies; no generic issue table is introduced."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import (
    HandlingStatus,
    ImportBatchStatus,
    ImportSourceType,
    MatchStatus,
    MonthlyImportBatch,
    MonthlyImportRow,
    ReconcileStatus,
    TicketStatus,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.business.work_ticket_management.schemas_workflow import (
    ReconcileCategory,
    ReconcileItemOut,
    ReconcileSearchIn,
    ReconcileSummaryOut,
)
from app.business.work_ticket_management.services.common import sqid
from app.business.work_ticket_management.services.master_data import get_month_unit
from app.utils import encode_id, get_db_conn

BLOCKING = {ReconcileCategory.ticket_without_order.value, ReconcileCategory.duplicate_code.value}
CATEGORY_ORDER = [
    ReconcileCategory.plan_missing_actual,
    ReconcileCategory.actual_missing_plan,
    ReconcileCategory.actual_without_ticket,
    ReconcileCategory.ticket_without_order,
    ReconcileCategory.duplicate_code,
    ReconcileCategory.unassigned,
    ReconcileCategory.no_time,
    ReconcileCategory.ambiguous,
    ReconcileCategory.cross_month_duplicate,
]


def _key(category: ReconcileCategory, entity: str, value: Any) -> str:
    return f"{entity}:{value}"


def _empty_counts() -> dict[str, int]:
    return {category.value: 0 for category in CATEGORY_ORDER}


async def _rows(month_id: int, source_type: ImportSourceType, db: BaseDBAsyncClient) -> list[MonthlyImportRow]:
    return list(
        await MonthlyImportRow
        .filter(
            batch__work_month_id=month_id,
            batch__status=ImportBatchStatus.active,
            batch__source_type=source_type,
        )
        .using_db(db)
        .exclude(handling_status=HandlingStatus.ignored)
        .select_related("order", "batch")
    )


async def _compute(month_id: int, db: BaseDBAsyncClient) -> dict[str, Any]:
    month, unit = await get_month_unit(month_id, db)
    plan = await _rows(month_id, ImportSourceType.plan, db)
    actual = await _rows(month_id, ImportSourceType.actual, db)
    plan_map: dict[str, list[MonthlyImportRow]] = defaultdict(list)
    actual_map: dict[str, list[MonthlyImportRow]] = defaultdict(list)
    for row in plan:
        plan_map[row.normalized_part_no].append(row)
    for row in actual:
        actual_map[row.normalized_part_no].append(row)
    tickets = list(await WorkTicket.filter(work_month_id=month_id, status=TicketStatus.active).using_db(db).exclude(reconcile_status=ReconcileStatus.ignored))
    all_tickets = list(await WorkTicket.filter(work_month_id=month_id, status=TicketStatus.active).using_db(db))
    ticket_order_ids = {ticket.order_id for ticket in all_tickets if ticket.order_id is not None}
    assigned_ids = set(await WorkTicketAssignment.filter(ticket__work_month_id=month_id, ticket__status=TicketStatus.active).using_db(db).values_list("ticket_id", flat=True))
    timed_ids = set(await WorkTimeEntry.filter(assignment__ticket__work_month_id=month_id, assignment__ticket__status=TicketStatus.active).using_db(db).values_list("assignment__ticket_id", flat=True))
    orphan_tickets = [ticket for ticket in tickets if ticket.order_id is None]
    unassigned = [ticket for ticket in tickets if ticket.id not in assigned_ids]
    no_time = [ticket for ticket in tickets if ticket.id in assigned_ids and ticket.id not in timed_ids]
    ambiguous = [row for row in [*plan, *actual] if row.match_status == MatchStatus.ambiguous]
    actual_without_ticket = [row for row in actual if row.order_id is not None and row.order_id not in ticket_order_ids]
    plan_missing = [row for row in plan if row.normalized_part_no not in actual_map]
    actual_missing = [row for row in actual if row.normalized_part_no not in plan_map]
    duplicates: dict[str, list[WorkTicket]] = defaultdict(list)
    for ticket in tickets:
        if ticket.ticket_code_key:
            duplicates[ticket.ticket_code_key].append(ticket)
    duplicate_groups = {key: value for key, value in duplicates.items() if len(value) > 1}
    current_keys = {ticket.ticket_code_key for ticket in tickets if ticket.ticket_code_key}
    cross_month: dict[str, list[str]] = defaultdict(list)
    if current_keys:
        others = (
            await WorkTicket
            .filter(
                ticket_code_key__in=list(current_keys),
                work_month__production_unit_id=unit.id,
                status=TicketStatus.active,
            )
            .using_db(db)
            .exclude(work_month_id=month_id)
            .select_related("work_month")
        )
        for ticket in others:
            cross_month[ticket.ticket_code_key].append(ticket.work_month.year_month)
    cross_tickets = [ticket for ticket in tickets if ticket.ticket_code_key in cross_month]
    counts = _empty_counts()
    counts[ReconcileCategory.plan_missing_actual.value] = len(plan_missing)
    counts[ReconcileCategory.actual_missing_plan.value] = len(actual_missing)
    counts[ReconcileCategory.actual_without_ticket.value] = len(actual_without_ticket)
    counts[ReconcileCategory.ticket_without_order.value] = len(orphan_tickets)
    counts[ReconcileCategory.duplicate_code.value] = len(duplicate_groups)
    counts[ReconcileCategory.unassigned.value] = len(unassigned)
    counts[ReconcileCategory.no_time.value] = len(no_time)
    counts[ReconcileCategory.ambiguous.value] = len(ambiguous)
    counts[ReconcileCategory.cross_month_duplicate.value] = len(cross_tickets)
    has_actual = await MonthlyImportBatch.filter(work_month_id=month_id, source_type=ImportSourceType.actual, status=ImportBatchStatus.active).using_db(db).exists()
    return {
        "month": month,
        "unit": unit,
        "counts": counts,
        "plan_missing": plan_missing,
        "actual_missing": actual_missing,
        "actual_without_ticket": actual_without_ticket,
        "orphan_tickets": orphan_tickets,
        "duplicate_groups": duplicate_groups,
        "unassigned": unassigned,
        "no_time": no_time,
        "ambiguous": ambiguous,
        "cross_tickets": cross_tickets,
        "cross_month": cross_month,
        "has_actual": has_actual,
    }


async def summary_counts(month_id: int, db: BaseDBAsyncClient | None = None) -> dict[str, int]:
    if db is None:
        async with in_transaction(get_db_conn(WorkTicket)) as connection:
            return await summary_counts(month_id, connection)
    data = await _compute(month_id, db)
    return data["counts"]


async def summary(month_id: int) -> ReconcileSummaryOut:
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        data = await _compute(month_id, db)
        counts = data["counts"]
        blocking = sum(counts[key] for key in BLOCKING)
        warnings = sum(value for key, value in counts.items() if key not in BLOCKING)
        return ReconcileSummaryOut(
            work_month_id=sqid(data["month"].id),
            status=data["month"].status,
            counts=counts,
            blocking=blocking,
            warnings=warnings,
            has_actual_batch=data["has_actual"],
        )


def _item(
    category: ReconcileCategory,
    key: str,
    title: str,
    *,
    detail: str | None = None,
    entity_type: str = "work_ticket",
    entity_id: str | None = None,
    actions: list[str] | None = None,
) -> ReconcileItemOut:
    return ReconcileItemOut(
        key=key,
        category=category,
        severity="blocking" if category.value in BLOCKING else "warning",
        entity_type=entity_type,
        entity_id=entity_id,
        title=title,
        detail=detail,
        actions=actions or [],
    )


async def search(month_id: int, payload: ReconcileSearchIn) -> tuple[int, list[ReconcileItemOut]]:
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        data = await _compute(month_id, db)
        category = payload.category
        if category == ReconcileCategory.plan_missing_actual:
            items = [
                _item(
                    category,
                    _key(category, "import_row", row.id),
                    row.raw_part_no,
                    detail="计划清单有，实际入库没有",
                    entity_type="import_row",
                    entity_id=encode_id(row.id),
                    actions=["ignore"],
                )
                for row in data["plan_missing"]
            ]
        elif category == ReconcileCategory.actual_missing_plan:
            items = [
                _item(
                    category,
                    _key(category, "import_row", row.id),
                    row.raw_part_no,
                    detail="实际入库有，计划清单遗漏",
                    entity_type="import_row",
                    entity_id=encode_id(row.id),
                    actions=["create_ticket", "ignore"],
                )
                for row in data["actual_missing"]
            ]
        elif category == ReconcileCategory.actual_without_ticket:
            items = [
                _item(
                    category,
                    _key(category, "import_row", row.id),
                    row.raw_part_no,
                    detail=f"实际入库已匹配订单 {getattr(row.order, 'order_no', '')}，但本月没有工票",
                    entity_type="import_row",
                    entity_id=encode_id(row.id),
                    actions=["create_ticket", "ignore"],
                )
                for row in data["actual_without_ticket"]
            ]
        elif category == ReconcileCategory.ticket_without_order:
            items = [
                _item(
                    category,
                    _key(category, "ticket", ticket.id),
                    ticket.ticket_code or ticket.part_no_snapshot or f"工票 {ticket.id}",
                    detail="工票未关联订单",
                    entity_id=encode_id(ticket.id),
                    actions=["match_order", "void", "ignore"],
                )
                for ticket in data["orphan_tickets"]
            ]
        elif category == ReconcileCategory.duplicate_code:
            items = [
                _item(
                    category,
                    _key(category, "ticket_code", key),
                    key,
                    detail=f"同月重复工票码 {len(group)} 张",
                    entity_type="ticket_code",
                    entity_id=key,
                    actions=["fix_code"],
                )
                for key, group in data["duplicate_groups"].items()
            ]
        elif category == ReconcileCategory.unassigned:
            items = [
                _item(
                    category,
                    _key(category, "ticket", ticket.id),
                    ticket.ticket_code or ticket.part_no_snapshot or f"工票 {ticket.id}",
                    detail="尚未分配生产人员",
                    entity_id=encode_id(ticket.id),
                    actions=["assign", "ignore"],
                )
                for ticket in data["unassigned"]
            ]
        elif category == ReconcileCategory.no_time:
            items = [
                _item(
                    category,
                    _key(category, "ticket", ticket.id),
                    ticket.ticket_code or ticket.part_no_snapshot or f"工票 {ticket.id}",
                    detail="已分配人员，但尚未登记工时",
                    entity_id=encode_id(ticket.id),
                    actions=["log_time", "ignore"],
                )
                for ticket in data["no_time"]
            ]
        elif category == ReconcileCategory.ambiguous:
            items = [
                _item(
                    category,
                    _key(category, "import_row", row.id),
                    row.raw_part_no,
                    detail="同项目号存在多个候选订单，尚未确认",
                    entity_type="import_row",
                    entity_id=encode_id(row.id),
                    actions=["match_order", "ignore"],
                )
                for row in data["ambiguous"]
            ]
        else:
            items = [
                _item(
                    category,
                    _key(category, "ticket", ticket.id),
                    ticket.ticket_code or f"工票 {ticket.id}",
                    detail=f"工票码也出现在月份: {', '.join(sorted(set(data['cross_month'].get(ticket.ticket_code_key, []))))}",
                    entity_id=encode_id(ticket.id),
                    actions=["fix_code", "ignore"],
                )
                for ticket in data["cross_tickets"]
            ]
        if payload.keyword:
            keyword = payload.keyword.lower()
            items = [item for item in items if keyword in item.title.lower() or keyword in (item.detail or "").lower()]
        total = len(items)
        start = (payload.current - 1) * payload.size
        return total, items[start : start + payload.size]
