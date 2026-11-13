"""Shared service helpers: actors, decimal formatting, locks and revisions."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q

from app.business.work_ticket_management.models import (
    TicketStatus,
    Worker,
    WorkMonth,
    WorkMonthAction,
    WorkMonthStatus,
    WorkMonthStatusLog,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.utils import BizError, Code, encode_id, get_current_user_id


def actor_name() -> str:
    user_id = get_current_user_id()
    return str(user_id) if user_id is not None else ""


def sqid(value: int | None) -> Any:
    """Encode an internal int for a Pydantic ``SqidId`` output field."""
    return encode_id(value) if value is not None else None


def sqids(values: Sequence[int]) -> list[Any]:
    return [encode_id(value) for value in values]


def format_decimal(value: Decimal | None, places: int) -> str:
    if value is None:
        return ""
    return format(value, f".{places}f")


def chunked(values: Sequence[Any], size: int = 500) -> Iterable[Sequence[Any]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def ensure_month_writable(month: WorkMonth) -> None:
    if month.status in (WorkMonthStatus.verified, WorkMonthStatus.closed):
        raise BizError(code=Code.WORK_MONTH_CLOSED, msg=f"{month.year_month} 已核对或关闭，请先重新打开")


async def lock_month(month_id: int, db: BaseDBAsyncClient, *, writable: bool = True) -> WorkMonth:
    month = await WorkMonth.filter(id=month_id).using_db(db).select_for_update().first()
    if month is None:
        raise BizError(code=Code.WORK_MONTH_NOT_FOUND, msg="月度任务不存在")
    if writable:
        ensure_month_writable(month)
    return month


async def lock_ticket(ticket_id: int, revision: int | None, db: BaseDBAsyncClient) -> WorkTicket:
    ticket = await WorkTicket.filter(id=ticket_id).using_db(db).select_for_update().first()
    if ticket is None:
        raise BizError(code=Code.WORK_TICKET_NOT_FOUND, msg="工票不存在")
    if ticket.status != TicketStatus.active:
        raise BizError(code=Code.WORK_TICKET_NOT_WRITABLE, msg="工票已作废，不能修改")
    if revision is not None and ticket.revision != revision:
        raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="工票已被其他操作修改，请重新加载")
    return ticket


async def bump_ticket(ticket: WorkTicket, db: BaseDBAsyncClient, actor: str, **fields: Any) -> int:
    """CAS update one ticket; caller must already hold its row lock."""
    new_revision = ticket.revision + 1
    changed = (
        await WorkTicket.filter(id=ticket.id, revision=ticket.revision, status=TicketStatus.active).using_db(db).update(revision=new_revision, updated_by=actor, updated_at=datetime.now(), **fields)
    )
    if changed != 1:
        raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="工票版本冲突，请重新加载")
    ticket.revision = new_revision
    for key, value in fields.items():
        setattr(ticket, key, value)
    return new_revision


async def bump_month(month: WorkMonth, db: BaseDBAsyncClient, actor: str, **fields: Any) -> int:
    new_revision = month.revision + 1
    changed = await WorkMonth.filter(id=month.id, revision=month.revision).using_db(db).update(revision=new_revision, updated_by=actor, updated_at=datetime.now(), **fields)
    if changed != 1:
        raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="月度任务已被其他操作修改，请重新加载")
    month.revision = new_revision
    for key, value in fields.items():
        setattr(month, key, value)
    return new_revision


async def log_month_status(
    month: WorkMonth,
    *,
    from_status: WorkMonthStatus | None,
    action: WorkMonthAction,
    actor: str,
    db: BaseDBAsyncClient,
    reason: str | None = None,
    summary: dict[str, Any] | None = None,
) -> None:
    await WorkMonthStatusLog.create(
        work_month_id=month.id,
        from_status=from_status,
        to_status=month.status,
        action=action,
        reason=reason,
        summary=summary,
        created_by=actor,
        updated_by=actor,
        using_db=db,
    )


async def start_month_if_draft(month: WorkMonth, db: BaseDBAsyncClient, actor: str) -> None:
    if month.status != WorkMonthStatus.draft:
        return
    old_status = month.status
    await bump_month(month, db, actor, status=WorkMonthStatus.in_progress)
    await log_month_status(month, from_status=old_status, action=WorkMonthAction.start, actor=actor, db=db)


async def get_worker_or_error(worker_id: int, db: BaseDBAsyncClient) -> Worker:
    worker = await Worker.filter(id=worker_id).using_db(db).first()
    if worker is None:
        raise BizError(code=Code.WORK_WORKER_NOT_FOUND, msg=f"人员不存在: {worker_id}")
    return worker


async def ensure_workers(worker_ids: Sequence[int], *, allow_disabled: bool, db: BaseDBAsyncClient) -> list[Worker]:
    unique_ids = list(dict.fromkeys(worker_ids))
    workers = await Worker.filter(id__in=unique_ids).using_db(db)
    by_id = {worker.id: worker for worker in workers}
    missing = [worker_id for worker_id in unique_ids if worker_id not in by_id]
    if missing:
        raise BizError(code=Code.WORK_WORKER_NOT_FOUND, msg=f"人员不存在: {', '.join(map(str, missing))}")
    disabled = [worker.name for worker in workers if not worker.enabled]
    if disabled and not allow_disabled:
        raise BizError(code=Code.WORK_TICKET_WORKER_DISABLED, msg=f"人员已停用: {', '.join(disabled)}")
    return [by_id[worker_id] for worker_id in unique_ids]


async def ticket_metrics(ticket_ids: Sequence[int], db: BaseDBAsyncClient) -> dict[int, dict[str, Any]]:
    """Batch load assignment/worker/time summaries for a page of tickets."""
    result: dict[int, dict[str, Any]] = {ticket_id: {"assignment_count": 0, "worker_names": [], "total_hours": Decimal("0.00"), "has_time": False} for ticket_id in ticket_ids}
    if not ticket_ids:
        return result
    assignments = await WorkTicketAssignment.filter(ticket_id__in=list(ticket_ids)).using_db(db).prefetch_related("worker")
    assignment_owner: dict[int, int] = {}
    for assignment in assignments:
        assignment_owner[assignment.id] = assignment.ticket_id
        item = result[assignment.ticket_id]
        item["assignment_count"] += 1
        if assignment.worker is not None:
            item["worker_names"].append(assignment.worker.name)
    entries = await WorkTimeEntry.filter(assignment_id__in=list(assignment_owner)).using_db(db).values("assignment_id", "hours")
    for entry in entries:
        ticket_id = assignment_owner.get(entry["assignment_id"])
        if ticket_id is None:
            continue
        item = result[ticket_id]
        item["total_hours"] += Decimal(entry["hours"])
        item["has_time"] = True
    for item in result.values():
        item["total_hours"] = item["total_hours"].quantize(Decimal("0.01"))
    return result


def text_search_q(keyword: str, fields: Sequence[str]) -> Q:
    q = Q()
    for field in fields:
        q |= Q(**{f"{field}__icontains": keyword})
    return q
