"""Work-time matrix and transactional batch entry."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import (
    TicketStatus,
    Worker,
    WorkMonth,
    WorkMonthStatus,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.business.work_ticket_management.rules import month_end, month_start
from app.business.work_ticket_management.schemas_workflow import (
    TimeBatchSaveIn,
    TimeBatchSaveOut,
    TimeBatchTicketResult,
    TimeEntryDeleteIn,
    TimeEntryOut,
    TimeEntrySearchIn,
    TimeEntryUpdateIn,
    TimeMatrixEntry,
    TimeMatrixIn,
    TimeMatrixOut,
    TimeMatrixTicket,
    WorkerOption,
)
from app.business.work_ticket_management.services.common import actor_name, bump_ticket, lock_month, lock_ticket, sqid
from app.business.work_ticket_management.services.master_data import get_month_unit
from app.utils import BizError, Code, get_db_conn


async def _validate_accounting_month(value: str | None, ticket_month: str, unit_id: int, db: BaseDBAsyncClient) -> str | None:
    if value is None or value == ticket_month:
        return value
    target = await WorkMonth.filter(year_month=value, production_unit_id=unit_id).using_db(db).first()
    if target is None:
        raise BizError(code=Code.WORK_TIME_ACCOUNTING_MONTH_INVALID, msg=f"归属月份 {value} 尚未创建")
    if target.status in (WorkMonthStatus.verified, WorkMonthStatus.closed):
        raise BizError(code=Code.WORK_TIME_ACCOUNTING_MONTH_INVALID, msg=f"归属月份 {value} 已核对或关闭")
    return value


async def _ensure_assignment(ticket: WorkTicket, worker_id: int, db: BaseDBAsyncClient, actor: str) -> WorkTicketAssignment:
    worker = await Worker.filter(id=worker_id).using_db(db).first()
    if worker is None:
        raise BizError(code=Code.WORK_WORKER_NOT_FOUND, msg="人员不存在")
    assignment, _ = await WorkTicketAssignment.get_or_create(
        ticket_id=ticket.id,
        worker_id=worker.id,
        defaults={"source": "time_entry", "created_by": actor, "updated_by": actor},
        using_db=db,
    )
    return assignment


async def matrix(payload: TimeMatrixIn) -> TimeMatrixOut:
    async with in_transaction(get_db_conn(WorkTimeEntry)) as db:
        month, unit = await get_month_unit(payload.work_month_id, db)
        ticket_query = WorkTicket.filter(work_month_id=month.id, status=TicketStatus.active)
        if payload.ticket_ids:
            ticket_query = ticket_query.filter(id__in=payload.ticket_ids)
        tickets = await ticket_query.using_db(db).order_by("id").limit(payload.ticket_limit + 1)
        truncated = len(tickets) > payload.ticket_limit
        tickets = tickets[: payload.ticket_limit]
        if payload.worker_ids:
            workers = await Worker.filter(id__in=payload.worker_ids).using_db(db)
        else:
            workers = await Worker.filter(production_unit_id=unit.id, enabled=True).using_db(db).order_by("name", "id").limit(50)
        worker_ids = [worker.id for worker in workers]
        ticket_ids = [ticket.id for ticket in tickets]
        start = payload.work_date_start or month_start(month.year_month)
        end = payload.work_date_end or month_end(month.year_month)
        entries: list[WorkTimeEntry] = []
        if ticket_ids and worker_ids:
            entries = list(
                await WorkTimeEntry
                .filter(
                    assignment__ticket_id__in=ticket_ids,
                    assignment__worker_id__in=worker_ids,
                    work_date__gte=start,
                    work_date__lte=end,
                )
                .using_db(db)
                .order_by("work_date", "id")
            )
        assignment_ids = {entry.assignment_id for entry in entries}
        assignments = {assignment.id: assignment for assignment in await WorkTicketAssignment.filter(id__in=list(assignment_ids)).using_db(db)} if assignment_ids else {}
        entry_rows = [
            TimeMatrixEntry(
                id=sqid(entry.id),
                ticket_id=sqid(assignments[entry.assignment_id].ticket_id),
                worker_id=sqid(assignments[entry.assignment_id].worker_id),
                work_date=entry.work_date,
                accounting_month=entry.accounting_month,
                hours=entry.hours,
            )
            for entry in entries
            if entry.assignment_id in assignments
        ]
        total = sum((entry.hours for entry in entries), Decimal("0.00")).quantize(Decimal("0.01"))
        return TimeMatrixOut(
            tickets=[
                TimeMatrixTicket(
                    id=sqid(ticket.id),
                    ticket_code=ticket.ticket_code,
                    part_no_snapshot=ticket.part_no_snapshot,
                    order_no_snapshot=ticket.order_no_snapshot,
                    name_snapshot=ticket.name_snapshot,
                    revision=ticket.revision,
                )
                for ticket in tickets
            ],
            workers=[WorkerOption(id=sqid(worker.id), worker_no=worker.worker_no, name=worker.name, production_unit_id=sqid(worker.production_unit_id), enabled=worker.enabled) for worker in workers],
            entries=entry_rows,
            total_hours=total,
            truncated=truncated,
        )


async def batch_save(payload: TimeBatchSaveIn) -> TimeBatchSaveOut:
    actor = actor_name()
    saved = deleted = 0
    async with in_transaction(get_db_conn(WorkTimeEntry)) as db:
        month = await lock_month(payload.work_month_id, db)
        _, unit = await get_month_unit(payload.work_month_id, db)
        ticket_ids = sorted({entry.ticket_id for entry in payload.entries})
        tickets = await WorkTicket.filter(id__in=ticket_ids, work_month_id=month.id, status=TicketStatus.active).using_db(db).order_by("id").select_for_update()
        by_id = {ticket.id: ticket for ticket in tickets}
        if len(by_id) != len(ticket_ids):
            raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="部分工票不存在、已作废或不属于当前月份")
        seen_cells: set[tuple[int, int, date]] = set()
        touched: set[int] = set()
        for entry in payload.entries:
            ticket = by_id[entry.ticket_id]
            if ticket.revision != entry.revision:
                raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="工票已被其他操作修改，请重新加载")
            cell = (entry.ticket_id, entry.worker_id, entry.work_date)
            if cell in seen_cells:
                raise BizError(code=Code.WORK_TIME_INVALID, msg="同一工票、人员、日期在本次提交中重复")
            seen_cells.add(cell)
            existing = await WorkTimeEntry.filter(id=entry.entry_id).using_db(db).select_for_update().first() if entry.entry_id else None
            if entry.entry_id and existing is None:
                raise BizError(code=Code.NOT_FOUND, msg="工时记录不存在")
            if entry.hours is None:
                if existing is not None:
                    await existing.delete(using_db=db)
                    deleted += 1
                    touched.add(ticket.id)
                continue
            assignment = await _ensure_assignment(ticket, entry.worker_id, db, actor)
            if existing is not None and existing.assignment_id != assignment.id:
                raise BizError(code=Code.WORK_TIME_INVALID, msg="工时记录不属于当前工票或人员")
            accounting = await _validate_accounting_month(entry.accounting_month, month.year_month, unit.id, db)
            if existing is None:
                existing = await WorkTimeEntry.filter(assignment_id=assignment.id, work_date=entry.work_date).using_db(db).select_for_update().first()
            if existing is not None:
                existing.work_date = entry.work_date
                existing.accounting_month = accounting
                existing.hours = entry.hours
                existing.updated_by = actor
                await existing.save(using_db=db)
            else:
                await WorkTimeEntry.create(
                    assignment_id=assignment.id,
                    work_date=entry.work_date,
                    accounting_month=accounting,
                    hours=entry.hours,
                    created_by=actor,
                    updated_by=actor,
                    using_db=db,
                )
            saved += 1
            touched.add(ticket.id)
        for ticket_id in sorted(touched):
            await bump_ticket(by_id[ticket_id], db, actor)
        totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        if touched:
            rows = await WorkTimeEntry.filter(assignment__ticket_id__in=list(touched)).using_db(db).values("assignment__ticket_id", "hours")
            for row in rows:
                totals[row["assignment__ticket_id"]] += Decimal(row["hours"])
        ticket_results = [TimeBatchTicketResult(ticket_id=sqid(ticket_id), revision=by_id[ticket_id].revision, total_hours=total.quantize(Decimal("0.01"))) for ticket_id, total in totals.items()]
    return TimeBatchSaveOut(saved_count=saved, deleted_count=deleted, tickets=ticket_results)


async def _entry_ticket(entry: WorkTimeEntry, db: BaseDBAsyncClient) -> tuple[WorkTicketAssignment, WorkTicket]:
    assignment = await WorkTicketAssignment.filter(id=entry.assignment_id).using_db(db).first()
    if assignment is None:
        raise BizError(code=Code.WORK_TICKET_ASSIGNMENT_NOT_FOUND, msg="工时对应的工票分配不存在")
    ticket = await WorkTicket.filter(id=assignment.ticket_id).using_db(db).first()
    if ticket is None:
        raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="工票不存在")
    return assignment, ticket


async def update_entry(entry_id: int, payload: TimeEntryUpdateIn) -> TimeEntryOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTimeEntry)) as db:
        entry = await WorkTimeEntry.filter(id=entry_id).using_db(db).select_for_update().first()
        if entry is None:
            raise BizError(code=Code.NOT_FOUND, msg="工时记录不存在")
        _, ticket = await _entry_ticket(entry, db)
        month = await lock_month(ticket.work_month_id, db)
        ticket = await lock_ticket(ticket.id, payload.revision, db)
        accounting = await _validate_accounting_month(payload.accounting_month, month.year_month, month.production_unit_id, db)
        conflict = await WorkTimeEntry.filter(assignment_id=entry.assignment_id, work_date=payload.work_date).exclude(id=entry.id).using_db(db).exists()
        if conflict:
            raise BizError(code=Code.WORK_TIME_INVALID, msg="该工票、人员、日期已有工时记录")
        entry.work_date = payload.work_date
        entry.accounting_month = accounting
        entry.hours = payload.hours
        entry.remark = payload.remark
        entry.updated_by = actor
        await entry.save(using_db=db)
        await bump_ticket(ticket, db, actor)
    return await _entry_out(entry_id)


async def delete_entry(entry_id: int, payload: TimeEntryDeleteIn) -> None:
    actor = actor_name()
    async with in_transaction(get_db_conn(WorkTimeEntry)) as db:
        entry = await WorkTimeEntry.filter(id=entry_id).using_db(db).select_for_update().first()
        if entry is None:
            raise BizError(code=Code.NOT_FOUND, msg="工时记录不存在")
        _, ticket = await _entry_ticket(entry, db)
        await lock_month(ticket.work_month_id, db)
        ticket = await lock_ticket(ticket.id, payload.revision, db)
        await entry.delete(using_db=db)
        await bump_ticket(ticket, db, actor)


async def _entry_out(entry_id: int) -> TimeEntryOut:
    async with in_transaction(get_db_conn(WorkTimeEntry)) as db:
        entry = await WorkTimeEntry.filter(id=entry_id).using_db(db).select_related("assignment__ticket__work_month", "assignment__worker").first()
        if entry is None:
            raise BizError(code=Code.NOT_FOUND, msg="工时记录不存在")
        return _entry_row(entry)


def _entry_row(entry: WorkTimeEntry) -> TimeEntryOut:
    assignment = entry.assignment
    ticket = assignment.ticket
    worker = assignment.worker
    month = ticket.work_month
    return TimeEntryOut(
        id=sqid(entry.id),
        ticket_id=sqid(ticket.id),
        ticket_code=ticket.ticket_code,
        part_no_snapshot=ticket.part_no_snapshot,
        order_no_snapshot=ticket.order_no_snapshot,
        worker_id=sqid(worker.id),
        worker_name=worker.name,
        work_date=entry.work_date,
        accounting_month=entry.accounting_month,
        effective_month=entry.accounting_month or month.year_month,
        hours=entry.hours,
        remark=entry.remark,
        revision=ticket.revision,
    )


async def list_entries(search: TimeEntrySearchIn) -> tuple[int, list[TimeEntryOut]]:
    async with in_transaction(get_db_conn(WorkTimeEntry)) as db:
        query = WorkTimeEntry.all()
        if search.work_month_id is not None:
            query = query.filter(assignment__ticket__work_month_id=search.work_month_id)
        if search.production_unit_id is not None:
            query = query.filter(assignment__ticket__work_month__production_unit_id=search.production_unit_id)
        if search.worker_id is not None:
            query = query.filter(assignment__worker_id=search.worker_id)
        if search.ticket_id is not None:
            query = query.filter(assignment__ticket_id=search.ticket_id)
        if search.work_date_start:
            query = query.filter(work_date__gte=search.work_date_start)
        if search.work_date_end:
            query = query.filter(work_date__lte=search.work_date_end)
        if search.accounting_month:
            query = query.filter(Q(accounting_month=search.accounting_month) | Q(accounting_month__isnull=True, assignment__ticket__work_month__year_month=search.accounting_month))
        total = await query.using_db(db).count()
        entries = (
            await query.using_db(db).select_related("assignment__ticket__work_month", "assignment__worker").order_by("-work_date", "-id").offset((search.current - 1) * search.size).limit(search.size)
        )
        return total, [_entry_row(entry) for entry in entries]
