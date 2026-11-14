"""Work ticket aggregate operations, code confirmation and OCR candidate lookup."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import (
    AssignmentSource,
    HandlingStatus,
    ImportBatchStatus,
    MatchSource,
    MatchStatus,
    MonthlyImportRow,
    ProductionUnit,
    ReconcileStatus,
    TicketCodeSource,
    TicketStatus,
    WorkMonth,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.business.work_ticket_management.rules import (
    RuleError,
    extract_ocr_tokens,
    get_rule,
    normalize_ticket_code,
    validate_ticket_code,
)
from app.business.work_ticket_management.schemas_workflow import (
    CodeConfirmIn,
    CodeConfirmOut,
    CodeLookupIn,
    CodeLookupOut,
    CodePasteIn,
    CodePasteOut,
    CodePreviewIn,
    CodePreviewOut,
    CodePreviewRow,
    OcrCandidateIn,
    OcrCandidateOut,
    TicketAssignIn,
    TicketAssignmentOut,
    TicketBatchAssignIn,
    TicketCreateIn,
    TicketDetailOut,
    TicketOut,
    TicketReconcileIn,
    TicketSearchIn,
    TicketTimeEntryOut,
    TicketUpdateIn,
    TicketVoidIn,
)
from app.business.work_ticket_management.services.common import (
    actor_name,
    bump_ticket,
    ensure_month_writable,
    ensure_workers,
    lock_month,
    lock_ticket,
    sqid,
    sqids,
    start_month_if_draft,
    ticket_metrics,
)
from app.business.work_ticket_management.services.master_data import ensure_order_mapping, get_month_unit
from app.business.work_ticket_management.services.order_access import get_order, order_snapshot, order_values
from app.utils import BizError, Code, get_db_conn, radar_log


async def _lock_ticket_with_month(ticket_id: int, revision: int, db: BaseDBAsyncClient) -> tuple[WorkTicket, WorkMonth]:
    """Lock month first, then ticket; every aggregate mutation uses this order."""
    ticket_month = await WorkTicket.filter(id=ticket_id).using_db(db).only("work_month_id").first()
    if ticket_month is None:
        raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="工票不存在")
    month = await lock_month(ticket_month.work_month_id, db)
    ticket = await lock_ticket(ticket_id, revision, db)
    return ticket, month


async def _unit(month: WorkMonth, db: BaseDBAsyncClient) -> ProductionUnit:
    unit = await ProductionUnit.filter(id=month.production_unit_id).using_db(db).first()
    if unit is None:
        raise BizError(code=Code.WORK_UNIT_IN_USE, msg="生产单位不存在")
    return unit


def _ticket_out(ticket: WorkTicket, month: WorkMonth, unit: ProductionUnit, metrics: dict[str, Any]) -> TicketOut:
    return TicketOut(
        id=sqid(ticket.id),
        work_month_id=sqid(ticket.work_month_id),
        year_month=month.year_month,
        production_unit_id=sqid(month.production_unit_id),
        production_unit_name=unit.name,
        order_id=sqid(ticket.order_id),
        order_no_snapshot=ticket.order_no_snapshot,
        part_no_snapshot=ticket.part_no_snapshot,
        name_snapshot=ticket.name_snapshot,
        ticket_code=ticket.ticket_code,
        code_source=ticket.code_source,
        code_confidence=ticket.code_confidence,
        status=ticket.status,
        reconcile_status=ticket.reconcile_status,
        reconcile_note=ticket.reconcile_note,
        assignment_count=int(metrics.get("assignment_count", 0)),
        worker_names=list(metrics.get("worker_names", [])),
        total_hours=metrics.get("total_hours", Decimal("0.00")),
        has_time=bool(metrics.get("has_time", False)),
        revision=ticket.revision,
        remark=ticket.remark,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


async def list_tickets(search: TicketSearchIn) -> tuple[int, list[TicketOut]]:
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        base = Q()
        if search.work_month_id is not None:
            base &= Q(work_month_id=search.work_month_id)
        if search.production_unit_id is not None:
            base &= Q(work_month__production_unit_id=search.production_unit_id)
        if search.year_month_start:
            base &= Q(work_month__year_month__gte=search.year_month_start)
        if search.year_month_end:
            base &= Q(work_month__year_month__lte=search.year_month_end)
        base &= Q(status=search.status if search.status is not None else TicketStatus.active)
        if search.reconcile_status is not None:
            base &= Q(reconcile_status=search.reconcile_status)
        if search.order_no:
            base &= Q(order_no_snapshot__icontains=search.order_no)
        if search.part_no:
            base &= Q(part_no_snapshot__icontains=search.part_no)
        if search.ticket_code:
            base &= Q(ticket_code__icontains=search.ticket_code)
        if search.keyword:
            base &= (
                Q(ticket_code__icontains=search.keyword) | Q(part_no_snapshot__icontains=search.keyword) | Q(order_no_snapshot__icontains=search.keyword) | Q(name_snapshot__icontains=search.keyword)
            )
        assigned_ids = await _assigned_ticket_ids(search, db)
        if search.assignment_status == "assigned":
            base &= Q(id__in=assigned_ids or [-1])
        elif search.assignment_status == "unassigned" and assigned_ids:
            base &= ~Q(id__in=assigned_ids)
        timed_ids = await _timed_ticket_ids(search, db)
        if search.time_status == "logged":
            base &= Q(id__in=timed_ids or [-1])
        elif search.time_status == "none" and timed_ids:
            base &= ~Q(id__in=timed_ids)
        query = WorkTicket.filter(base).using_db(db)
        total = await query.count()
        tickets = await query.order_by(*_ticket_order(search.order_by)).offset((search.current - 1) * search.size).limit(search.size)
        month_ids = list({ticket.work_month_id for ticket in tickets})
        months = {month.id: month for month in await WorkMonth.filter(id__in=month_ids).using_db(db).select_related("production_unit")} if month_ids else {}
        metrics = await ticket_metrics([ticket.id for ticket in tickets], db)
        records: list[TicketOut] = []
        for ticket in tickets:
            month = months.get(ticket.work_month_id)
            unit = month.production_unit if month is not None else None
            if month is not None and unit is not None:
                records.append(_ticket_out(ticket, month, unit, metrics.get(ticket.id, {})))
        return total, records


def _ticket_order(order_by: list[str] | None) -> list[str]:
    allowed = {"id", "ticket_code", "part_no_snapshot", "order_no_snapshot", "status", "reconcile_status", "revision", "created_at", "updated_at"}
    result = [value for value in (order_by or []) if value.lstrip("-") in allowed]
    return result or ["-id"]


async def _assigned_ticket_ids(search: TicketSearchIn, db: BaseDBAsyncClient) -> list[int]:
    query = WorkTicketAssignment.filter(ticket__status=TicketStatus.active)
    if search.work_month_id is not None:
        query = query.filter(ticket__work_month_id=search.work_month_id)
    if search.production_unit_id is not None:
        query = query.filter(ticket__work_month__production_unit_id=search.production_unit_id)
    if search.year_month_start:
        query = query.filter(ticket__work_month__year_month__gte=search.year_month_start)
    if search.year_month_end:
        query = query.filter(ticket__work_month__year_month__lte=search.year_month_end)
    rows = await query.using_db(db).values("ticket_id")
    return list({row["ticket_id"] for row in rows})


async def _timed_ticket_ids(search: TicketSearchIn, db: BaseDBAsyncClient) -> list[int]:
    query = WorkTimeEntry.filter(assignment__ticket__status=TicketStatus.active)
    if search.work_month_id is not None:
        query = query.filter(assignment__ticket__work_month_id=search.work_month_id)
    if search.production_unit_id is not None:
        query = query.filter(assignment__ticket__work_month__production_unit_id=search.production_unit_id)
    if search.year_month_start:
        query = query.filter(assignment__ticket__work_month__year_month__gte=search.year_month_start)
    if search.year_month_end:
        query = query.filter(assignment__ticket__work_month__year_month__lte=search.year_month_end)
    rows = await query.using_db(db).values("assignment__ticket_id")
    return list({row["assignment__ticket_id"] for row in rows})


async def detail(ticket_id: int, db: BaseDBAsyncClient | None = None) -> TicketDetailOut:
    if db is None:
        async with in_transaction(get_db_conn(WorkTicket)) as connection:
            return await detail(ticket_id, connection)
    ticket = await WorkTicket.filter(id=ticket_id).using_db(db).first()
    if ticket is None:
        raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="工票不存在")
    month, unit = await get_month_unit(ticket.work_month_id, db)
    metrics = (await ticket_metrics([ticket.id], db)).get(ticket.id, {})
    assignments = await WorkTicketAssignment.filter(ticket_id=ticket.id).using_db(db).prefetch_related("worker").order_by("id")
    assignment_by_id = {assignment.id: assignment for assignment in assignments}
    assignment_rows: list[TicketAssignmentOut] = []
    for assignment in assignments:
        worker = assignment.worker
        if worker is None:
            continue
        assignment_rows.append(
            TicketAssignmentOut(
                id=sqid(assignment.id),
                worker_id=sqid(worker.id),
                worker_no=worker.worker_no,
                worker_name=worker.name,
                worker_enabled=worker.enabled,
                source=assignment.source,
                remark=assignment.remark,
            )
        )
    entries = await WorkTimeEntry.filter(assignment_id__in=list(assignment_by_id)).using_db(db).order_by("work_date", "id")
    entry_rows: list[TicketTimeEntryOut] = []
    for entry in entries:
        assignment = assignment_by_id.get(entry.assignment_id)
        if assignment is None or assignment.worker is None:
            continue
        entry_rows.append(
            TicketTimeEntryOut(
                id=sqid(entry.id),
                worker_id=sqid(assignment.worker_id),
                worker_name=assignment.worker.name,
                work_date=entry.work_date,
                accounting_month=entry.accounting_month,
                hours=entry.hours,
                remark=entry.remark,
            )
        )
    base = _ticket_out(ticket, month, unit, metrics)
    return TicketDetailOut(**base.model_dump(mode="json"), assignments=assignment_rows, time_entries=entry_rows)


async def _resolve_source_row(month_id: int, row_id: int, db: BaseDBAsyncClient) -> MonthlyImportRow:
    row = await MonthlyImportRow.filter(id=row_id, batch__work_month_id=month_id, batch__status=ImportBatchStatus.active).using_db(db).first()
    if row is None:
        raise BizError(code=Code.WORK_IMPORT_ROW_NOT_FOUND, msg="来源导入行不存在或不属于当前月份")
    return row


async def _create_ticket_row(
    *,
    month: WorkMonth,
    unit: ProductionUnit,
    payload: TicketCreateIn,
    actor: str,
    db: BaseDBAsyncClient,
    code: str | None = None,
    code_source: TicketCodeSource | None = None,
) -> WorkTicket:
    source_row = await _resolve_source_row(month.id, payload.source_import_row_id, db) if payload.source_import_row_id else None
    order = None
    if payload.order_id is not None:
        order = await get_order(payload.order_id, db)
        if order is None:
            raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="订单不存在")
    elif source_row is not None and source_row.order_id is not None:
        order = await get_order(source_row.order_id, db)
    if order is not None:
        await ensure_order_mapping(order.id, unit.id, db, actor, allow_add_mapping=payload.allow_add_mapping)
    part_no = payload.part_no_snapshot or (source_row.normalized_part_no if source_row is not None else None)
    if order is None and not part_no:
        raise BizError(code=Code.WORK_TICKET_ORDER_REQUIRED, msg="工票必须关联订单或填写项目号")
    code_value = payload.ticket_code if code is None else code
    try:
        display, key = validate_ticket_code(code_value, get_rule()) if code_value else (None, None)
    except RuleError as exc:
        raise BizError(code=Code.WORK_TICKET_CODE_INVALID, msg=str(exc)) from exc
    if key and await WorkTicket.filter(work_month_id=month.id, ticket_code_key=key).using_db(db).exists():
        raise BizError(code=Code.WORK_TICKET_CODE_CONFLICT, msg=f"工票码 {display} 在当前月份已存在")
    snapshots = order_values(order) if order is not None else {"order_no_snapshot": None, "part_no_snapshot": part_no, "name_snapshot": payload.name_snapshot}
    ticket = await WorkTicket.create(
        work_month_id=month.id,
        order_id=order.id if order is not None else None,
        ticket_code=display,
        ticket_code_key=key,
        code_source=(code_source or (TicketCodeSource.manual if display else TicketCodeSource.none)),
        code_confidence=payload.code_confidence if display else None,
        source_import_row_id=source_row.id if source_row is not None else None,
        status=TicketStatus.active,
        reconcile_status=ReconcileStatus.pending,
        remark=payload.remark,
        revision=1,
        created_by=actor,
        updated_by=actor,
        using_db=db,
        **snapshots,
    )
    if payload.worker_ids:
        workers = await ensure_workers(payload.worker_ids, allow_disabled=payload.allow_disabled_workers, db=db)
        for worker in workers:
            await WorkTicketAssignment.get_or_create(
                ticket_id=ticket.id,
                worker_id=worker.id,
                defaults={"source": AssignmentSource.manual, "created_by": actor, "updated_by": actor},
                using_db=db,
            )
    if source_row is not None:
        if order is not None:
            source_row.order_id = order.id
            source_row.match_status = MatchStatus.matched
            source_row.match_source = MatchSource.manual
        source_row.handling_status = HandlingStatus.resolved
        source_row.handled_at = datetime.now()
        source_row.handled_by = actor
        source_row.updated_by = actor
        await source_row.save(using_db=db)
    return ticket


async def create_ticket(payload: TicketCreateIn) -> TicketDetailOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        month = await lock_month(payload.work_month_id, db)
        unit = await _unit(month, db)
        await start_month_if_draft(month, db, actor)
        ticket = await _create_ticket_row(month=month, unit=unit, payload=payload, actor=actor, db=db)
        ticket_id = ticket.id
    radar_log("创建工票", data={"ticketId": ticket_id, "workMonthId": payload.work_month_id})
    return await detail(ticket_id)


async def update_ticket(ticket_id: int, payload: TicketUpdateIn) -> TicketDetailOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        ticket, month = await _lock_ticket_with_month(ticket_id, payload.revision, db)
        unit = await _unit(month, db)
        updates: dict[str, Any] = {}
        if "order_id" in payload.model_fields_set:
            if payload.order_id is None:
                updates["order_id"] = None
            else:
                order = await get_order(payload.order_id, db)
                if order is None:
                    raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="订单不存在")
                await ensure_order_mapping(order.id, unit.id, db, actor, allow_add_mapping=payload.allow_add_mapping)
                updates.update(order_values(order))
                updates["order_id"] = order.id
        if "ticket_code" in payload.model_fields_set:
            try:
                display, key = validate_ticket_code(payload.ticket_code, get_rule())
            except RuleError as exc:
                raise BizError(code=Code.WORK_TICKET_CODE_INVALID, msg=str(exc)) from exc
            if key:
                conflict = await WorkTicket.filter(work_month_id=month.id, ticket_code_key=key).exclude(id=ticket.id).using_db(db).exists()
                if conflict:
                    raise BizError(code=Code.WORK_TICKET_CODE_CONFLICT, msg=f"工票码 {display} 在当前月份已存在")
            updates["ticket_code"] = display
            updates["ticket_code_key"] = key
            updates["code_source"] = (payload.code_source or (TicketCodeSource.manual if display else TicketCodeSource.none)) if display else TicketCodeSource.none
            updates["code_confidence"] = None
        if "remark" in payload.model_fields_set:
            updates["remark"] = payload.remark
        if payload.reconcile_status is not None:
            updates["reconcile_status"] = payload.reconcile_status
            updates["reconcile_note"] = payload.reconcile_note
        await bump_ticket(ticket, db, actor, **updates)
    radar_log("更新工票", data={"ticketId": ticket_id})
    return await detail(ticket_id)


async def void_ticket(ticket_id: int, payload: TicketVoidIn) -> TicketDetailOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        ticket, _ = await _lock_ticket_with_month(ticket_id, payload.revision, db)
        await bump_ticket(ticket, db, actor, status=TicketStatus.void, void_reason=payload.reason, voided_at=datetime.now(), voided_by=actor)
    radar_log("作废工票", data={"ticketId": ticket_id})
    return await detail(ticket_id)


async def assign_workers(ticket_id: int, payload: TicketAssignIn) -> TicketDetailOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        ticket, _ = await _lock_ticket_with_month(ticket_id, payload.revision, db)
        workers = await ensure_workers(payload.worker_ids, allow_disabled=payload.allow_disabled, db=db)
        created = 0
        for worker in workers:
            _, was_created = await WorkTicketAssignment.get_or_create(
                ticket_id=ticket.id,
                worker_id=worker.id,
                defaults={"source": payload.source, "created_by": actor, "updated_by": actor},
                using_db=db,
            )
            created += int(was_created)
        if created:
            await bump_ticket(ticket, db, actor)
    return await detail(ticket_id)


async def remove_assignment(ticket_id: int, worker_id: int, revision: int) -> TicketDetailOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        ticket, _ = await _lock_ticket_with_month(ticket_id, revision, db)
        assignment = await WorkTicketAssignment.filter(ticket_id=ticket.id, worker_id=worker_id).using_db(db).first()
        if assignment is None:
            raise BizError(code=Code.WORK_TICKET_ASSIGNMENT_NOT_FOUND, msg="工票分配不存在")
        if await WorkTimeEntry.filter(assignment_id=assignment.id).using_db(db).exists():
            raise BizError(code=Code.WORK_TICKET_ASSIGNMENT_HAS_TIME, msg="该人员已有工时记录，请先删除工时")
        await assignment.delete(using_db=db)
        await bump_ticket(ticket, db, actor)
    return await detail(ticket_id)


async def batch_assign(payload: TicketBatchAssignIn) -> dict[str, int]:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        month_ids = list(set(await WorkTicket.filter(id__in=payload.ticket_ids).using_db(db).values_list("work_month_id", flat=True)))
        months = await WorkMonth.filter(id__in=month_ids).using_db(db).order_by("id").select_for_update()
        for month in months:
            ensure_month_writable(month)
        tickets = await WorkTicket.filter(id__in=payload.ticket_ids, status=TicketStatus.active).using_db(db).order_by("id").select_for_update()
        if len(tickets) != len(set(payload.ticket_ids)):
            raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="部分工票不存在或已作废")
        workers = await ensure_workers(payload.worker_ids, allow_disabled=payload.allow_disabled, db=db)
        created = 0
        for ticket in tickets:
            ticket_created = 0
            for worker in workers:
                _, was_created = await WorkTicketAssignment.get_or_create(
                    ticket_id=ticket.id,
                    worker_id=worker.id,
                    defaults={"source": AssignmentSource.batch, "created_by": actor, "updated_by": actor},
                    using_db=db,
                )
                ticket_created += int(was_created)
            if ticket_created:
                created += ticket_created
                await bump_ticket(ticket, db, actor)
    return {"tickets": len(tickets), "assignments": created}


async def reconcile_ticket(ticket_id: int, payload: TicketReconcileIn) -> TicketDetailOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        ticket, _ = await _lock_ticket_with_month(ticket_id, payload.revision, db)
        await bump_ticket(ticket, db, actor, reconcile_status=payload.status, reconcile_note=payload.note)
    return await detail(ticket_id)


async def _resolve_code_item(item: Any, month: WorkMonth, db: BaseDBAsyncClient) -> tuple[Any, MonthlyImportRow | None]:
    if item.order_id is not None:
        order = await get_order(item.order_id, db)
        if order is None:
            raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="订单不存在")
        return order, None
    if item.source_import_row_id is not None:
        row = await _resolve_source_row(month.id, item.source_import_row_id, db)
        if row.order_id is not None:
            order = await get_order(row.order_id, db)
            if order is None:
                raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="订单不存在")
            return order, row
        return None, row
    raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="候选未指定订单或导入行")


async def preview_codes(payload: CodePreviewIn) -> CodePreviewOut:
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        month, _ = await get_month_unit(payload.work_month_id, db)
        rule = get_rule(payload.rule_name)
        rows: list[CodePreviewRow] = []
        conflicts = 0
        for item in payload.items:
            try:
                order, row = await _resolve_code_item(item, month, db)
            except BizError as exc:
                rows.append(
                    CodePreviewRow(
                        order_id=sqid(item.order_id),
                        source_import_row_id=sqid(item.source_import_row_id),
                        order_no=None,
                        part_no=None,
                        name=None,
                        preview_code=None,
                        valid=False,
                        error=exc.msg,
                        conflict_ticket_id=None,
                        conflict_code=None,
                    )
                )
                continue
            preview_code = None
            error = None
            if rule is None:
                error = "尚未配置工票码规则，请手工录入"
            elif order is None:
                error = "未找到订单"
            else:
                try:
                    preview_code = rule.preview(order_snapshot(order), item.sequence)
                except RuleError as exc:
                    error = str(exc)
            conflict = None
            if preview_code:
                _, key = normalize_ticket_code(preview_code)
                conflict = await WorkTicket.filter(work_month_id=month.id, ticket_code_key=key).using_db(db).first()
                if conflict:
                    conflicts += 1
            rows.append(
                CodePreviewRow(
                    order_id=sqid(order.id if order is not None else None),
                    source_import_row_id=sqid(item.source_import_row_id),
                    order_no=getattr(order, "order_no", None) if order is not None else None,
                    part_no=getattr(order, "part_no", None) if order is not None else (row.normalized_part_no if row is not None else None),
                    name=getattr(order, "name", None) if order is not None else None,
                    preview_code=preview_code,
                    valid=bool(preview_code and not error and not conflict),
                    error=error or ("工票码已存在" if conflict else None),
                    conflict_ticket_id=sqid(conflict.id if conflict else None),
                    conflict_code=conflict.ticket_code if conflict else None,
                )
            )
        return CodePreviewOut(configured=rule is not None, rule_name=rule.name if rule else None, rows=rows, conflicts=conflicts)


async def confirm_codes(payload: CodeConfirmIn) -> CodeConfirmOut:
    actor = actor_name()
    created_ids: list[int] = []
    skipped = 0
    conflicts: list[str] = []
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        month = await lock_month(payload.work_month_id, db)
        unit = await _unit(month, db)
        rule = get_rule(payload.rule_name)
        await start_month_if_draft(month, db, actor)
        for item in payload.items:
            try:
                order, row = await _resolve_code_item(item, month, db)
            except BizError as exc:
                conflicts.append(exc.msg)
                continue
            code = item.code
            if code is None and rule is not None and order is not None:
                try:
                    code = rule.preview(order_snapshot(order), item.sequence)
                except RuleError as exc:
                    conflicts.append(str(exc))
                    continue
            if not code:
                conflicts.append("尚未配置工票码规则，请手工录入")
                continue
            try:
                display, key = validate_ticket_code(code, rule)
            except RuleError as exc:
                conflicts.append(str(exc))
                continue
            if key and await WorkTicket.filter(work_month_id=month.id, ticket_code_key=key).using_db(db).exists():
                skipped += 1
                continue
            if (
                item.source_import_row_id is not None
                and await WorkTicket.filter(work_month_id=month.id, source_import_row_id=item.source_import_row_id, status=TicketStatus.active).using_db(db).exists()
            ):
                skipped += 1
                continue
            ticket_payload = TicketCreateIn(
                work_month_id=month.id,
                order_id=order.id if order is not None else None,
                source_import_row_id=item.source_import_row_id,
                part_no_snapshot=row.normalized_part_no if row is not None else None,
                ticket_code=display,
                code_source=TicketCodeSource.manual if item.code is not None else TicketCodeSource.auto,
                code_confidence=None,
                remark=None,
                name_snapshot=None,
                allow_add_mapping=payload.allow_add_mapping,
            )
            ticket = await _create_ticket_row(
                month=month,
                unit=unit,
                payload=ticket_payload,
                actor=actor,
                db=db,
                code=display,
                code_source=ticket_payload.code_source,
            )
            created_ids.append(ticket.id)
    return CodeConfirmOut(created_count=len(created_ids), skipped_count=skipped, ticket_ids=sqids(created_ids), conflicts=conflicts)


async def paste_codes(payload: CodePasteIn) -> CodePasteOut:
    actor = actor_name()
    ticket_ids = [item.ticket_id for item in payload.items]
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        month_ids = list(set(await WorkTicket.filter(id__in=ticket_ids).using_db(db).values_list("work_month_id", flat=True)))
        months = await WorkMonth.filter(id__in=month_ids).using_db(db).order_by("id").select_for_update()
        for month in months:
            ensure_month_writable(month)
        tickets = await WorkTicket.filter(id__in=ticket_ids, status=TicketStatus.active).using_db(db).order_by("id").select_for_update()
        by_id = {ticket.id: ticket for ticket in tickets}
        if len(by_id) != len(set(ticket_ids)):
            raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="部分工票不存在或已作废")
        prepared: dict[int, tuple[str | None, str | None]] = {}
        seen_keys: set[str] = set()
        for item in payload.items:
            ticket = by_id[item.ticket_id]
            if ticket.revision != item.revision:
                raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg=f"工票 {ticket.ticket_code or ticket.id} 已被修改")
            try:
                display, key = validate_ticket_code(item.code, get_rule())
            except RuleError as exc:
                raise BizError(code=Code.WORK_TICKET_CODE_INVALID, msg=str(exc)) from exc
            if not key:
                raise BizError(code=Code.WORK_TICKET_CODE_INVALID, msg="工票码不能为空")
            if key in seen_keys:
                raise BizError(code=Code.WORK_TICKET_CODE_CONFLICT, msg=f"工票码 {display} 在本次提交中重复")
            seen_keys.add(key)
            conflict = await WorkTicket.filter(work_month_id=ticket.work_month_id, ticket_code_key=key).exclude(id=ticket.id).using_db(db).exists()
            if conflict:
                raise BizError(code=Code.WORK_TICKET_CODE_CONFLICT, msg=f"工票码 {display} 在当前月份已存在")
            prepared[ticket.id] = (display, key)
        for ticket in tickets:
            display, key = prepared[ticket.id]
            await bump_ticket(ticket, db, actor, ticket_code=display, ticket_code_key=key, code_source=TicketCodeSource.manual, code_confidence=None)
    return CodePasteOut(updated_count=len(prepared))


async def _lookup_codes(month_id: int, codes: list[str], include_other_months: bool, db: BaseDBAsyncClient) -> list[CodeLookupOut]:
    month, unit = await get_month_unit(month_id, db)
    rule = get_rule()
    result: list[CodeLookupOut] = []
    seen: set[str] = set()
    for code in codes:
        try:
            _, key = validate_ticket_code(code, rule)
        except RuleError:
            result.append(CodeLookupOut(code=code, normalized=normalize_ticket_code(code)[1] or "", valid=False))
            continue
        normalized = key or ""
        if normalized in seen:
            continue
        seen.add(normalized)
        ticket = await WorkTicket.filter(work_month_id=month.id, ticket_code_key=normalized, status=TicketStatus.active).using_db(db).first()
        ticket_month = await WorkMonth.filter(id=ticket.work_month_id).using_db(db).first() if ticket is not None else None
        other: list[dict[str, Any]] = []
        if ticket is None and include_other_months and normalized:
            others = (
                await WorkTicket
                .filter(ticket_code_key=normalized, work_month__production_unit_id=unit.id, status=TicketStatus.active)
                .using_db(db)
                .exclude(work_month_id=month.id)
                .order_by("-work_month__year_month")
                .limit(10)
                .values("id", "ticket_code", "work_month__year_month", "status")
            )
            for item in others:
                other.append({"ticketId": item["id"], "ticketCode": item["ticket_code"], "yearMonth": item["work_month__year_month"], "status": str(item["status"])})
        result.append(
            CodeLookupOut(
                code=code,
                normalized=normalized,
                valid=True,
                ticket_id=sqid(ticket.id if ticket else None),
                ticket_code=ticket.ticket_code if ticket else None,
                part_no=ticket.part_no_snapshot if ticket else None,
                order_no=ticket.order_no_snapshot if ticket else None,
                ticket_status=ticket.status if ticket else None,
                work_month_id=sqid(ticket.work_month_id if ticket else None),
                year_month=ticket_month.year_month if ticket_month is not None else None,
                work_month_status=ticket_month.status if ticket_month is not None else None,
                other_month_matches=other,
            )
        )
    return result


async def code_lookup(payload: CodeLookupIn) -> list[CodeLookupOut]:
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        return await _lookup_codes(payload.work_month_id, payload.codes, payload.include_other_months, db)


async def ocr_candidates(payload: OcrCandidateIn) -> list[OcrCandidateOut]:
    tokens = extract_ocr_tokens(payload.text, numeric_mode=payload.numeric_mode)
    if not tokens:
        raise BizError(code=Code.WORK_OCR_TEXT_INVALID, msg="未从 OCR 文本中识别到候选工票码")
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        lookups = await _lookup_codes(payload.work_month_id, [normalized for _, normalized in tokens], True, db)
        by_code = {item.normalized: item for item in lookups}
        seen: set[str] = set()
        result: list[OcrCandidateOut] = []
        for original, normalized in tokens:
            duplicate = normalized in seen
            seen.add(normalized)
            match = by_code.get(normalized)
            result.append(OcrCandidateOut(original=original, normalized=normalized, confidence=None, valid=bool(match and match.valid), duplicate=duplicate, match=match))
        return result
