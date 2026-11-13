"""Monthly task lifecycle and summary."""

from __future__ import annotations

from datetime import datetime

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import (
    ImportBatchStatus,
    ImportSourceType,
    MatchStatus,
    MonthlyImportBatch,
    MonthlyImportRow,
    TicketStatus,
    WorkMonth,
    WorkMonthAction,
    WorkMonthStatus,
    WorkMonthStatusLog,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.business.work_ticket_management.schemas_workflow import (
    WorkMonthCloseIn,
    WorkMonthOpenIn,
    WorkMonthStatusLogOut,
    WorkMonthSummaryOut,
)
from app.business.work_ticket_management.services.common import (
    actor_name,
    bump_month,
    lock_month,
    log_month_status,
    sqid,
)
from app.utils import BizError, Code, get_db_conn


async def summary(month_id: int, db: BaseDBAsyncClient | None = None) -> WorkMonthSummaryOut:
    query = WorkMonth.filter(id=month_id)
    if db is not None:
        query = query.using_db(db)
    month = await query.select_related("production_unit").first()
    if month is None:
        raise BizError(code=Code.WORK_MONTH_NOT_FOUND, msg="月度任务不存在")
    unit = month.production_unit
    rows = MonthlyImportRow.filter(batch__work_month_id=month_id, batch__status=ImportBatchStatus.active)
    tickets = WorkTicket.filter(work_month_id=month_id, status=TicketStatus.active)
    row_count = await rows.count()
    matched_rows = await rows.filter(match_status=MatchStatus.matched).count()
    ambiguous_rows = await rows.filter(match_status=MatchStatus.ambiguous).count()
    ticket_count = await tickets.count()
    assigned_ids = set(await WorkTicketAssignment.filter(ticket__work_month_id=month_id, ticket__status=TicketStatus.active).values_list("ticket_id", flat=True))
    timed_ids = set(await WorkTimeEntry.filter(assignment__ticket__work_month_id=month_id, assignment__ticket__status=TicketStatus.active).values_list("assignment__ticket_id", flat=True))
    has_actual = await MonthlyImportBatch.filter(work_month_id=month_id, source_type=ImportSourceType.actual, status=ImportBatchStatus.active).exists()
    # Imported lazily to avoid a module cycle with reconciliation.
    from app.business.work_ticket_management.services.reconciliation import summary_counts

    counts = await summary_counts(month_id)
    anomaly_count = sum(counts.values())
    return WorkMonthSummaryOut(
        id=sqid(month.id),
        year_month=month.year_month,
        production_unit_id=sqid(month.production_unit_id),
        production_unit_name=unit.name if unit is not None else "",
        status=month.status,
        revision=month.revision,
        row_count=row_count,
        matched_rows=matched_rows,
        ambiguous_rows=ambiguous_rows,
        ticket_count=ticket_count,
        assigned_ticket_count=len(assigned_ids),
        timed_ticket_count=len(timed_ids),
        anomaly_count=anomaly_count,
        has_actual_batch=has_actual,
        closed_at=month.closed_at,
    )


async def open_month(payload: WorkMonthOpenIn, actor: str) -> WorkMonthSummaryOut:
    async with in_transaction(get_db_conn(WorkMonth)) as db:
        from app.business.work_ticket_management.models import ProductionUnit

        unit = await ProductionUnit.filter(id=payload.production_unit_id).using_db(db).first()
        if unit is None:
            raise BizError(code=Code.WORK_UNIT_IN_USE, msg="生产单位不存在")
        month = await WorkMonth.filter(year_month=payload.year_month, production_unit_id=payload.production_unit_id).using_db(db).first()
        if month is None:
            if not unit.enabled:
                raise BizError(code=Code.WORK_UNIT_IN_USE, msg="生产单位已停用，不能新建月度任务")
            month = await WorkMonth.create(
                year_month=payload.year_month,
                production_unit_id=payload.production_unit_id,
                status=WorkMonthStatus.draft,
                revision=1,
                created_by=actor,
                updated_by=actor,
                using_db=db,
            )
            await log_month_status(month, from_status=None, action=WorkMonthAction.open, actor=actor, db=db)
    return await summary(month.id)


async def detail(month_id: int) -> WorkMonthSummaryOut:
    return await summary(month_id)


async def list_status_logs(month_id: int) -> list[WorkMonthStatusLogOut]:
    logs = await WorkMonthStatusLog.filter(work_month_id=month_id).order_by("id")
    return [
        WorkMonthStatusLogOut(
            id=sqid(log.id),
            from_status=log.from_status,
            to_status=log.to_status,
            action=log.action.value if hasattr(log.action, "value") else str(log.action),
            reason=log.reason,
            created_by=log.created_by,
            created_at=log.created_at,
        )
        for log in logs
    ]


async def _blocking_counts(month_id: int) -> dict[str, int]:
    from app.business.work_ticket_management.services.reconciliation import summary_counts

    return await summary_counts(month_id)


async def verify_month(month_id: int, revision: int, reason: str | None, actor: str) -> WorkMonthSummaryOut:
    async with in_transaction(get_db_conn(WorkMonth)) as db:
        month = await lock_month(month_id, db, writable=False)
        if month.revision != revision:
            raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="月度任务已被修改，请重新加载")
        if month.status != WorkMonthStatus.in_progress:
            raise BizError(code=Code.WORK_MONTH_STATE_INVALID, msg="只有进行中的月度任务可以核对")
        counts = await _blocking_counts(month_id)
        blocking = counts.get("ticket_without_order", 0) + counts.get("duplicate_code", 0)
        if blocking:
            raise BizError(code=Code.WORK_RECONCILE_BLOCKED, msg=f"仍有 {blocking} 项阻断异常，请先处理")
        old = month.status
        await bump_month(month, db, actor, status=WorkMonthStatus.verified)
        await log_month_status(month, from_status=old, action=WorkMonthAction.verify, actor=actor, db=db, reason=reason, summary=counts)
    return await summary(month_id)


async def close_month(month_id: int, payload: WorkMonthCloseIn, actor: str) -> WorkMonthSummaryOut:
    async with in_transaction(get_db_conn(WorkMonth)) as db:
        month = await lock_month(month_id, db, writable=False)
        if month.revision != payload.revision:
            raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="月度任务已被修改，请重新加载")
        if month.status != WorkMonthStatus.verified:
            raise BizError(code=Code.WORK_MONTH_STATE_INVALID, msg="只有已核对的月度任务可以关闭")
        counts = await _blocking_counts(month_id)
        blocking = counts.get("ticket_without_order", 0) + counts.get("duplicate_code", 0)
        if blocking:
            raise BizError(code=Code.WORK_RECONCILE_BLOCKED, msg=f"仍有 {blocking} 项阻断异常，请先处理")
        warnings = sum(value for key, value in counts.items() if key not in {"ticket_without_order", "duplicate_code"})
        if warnings and not payload.confirm_warnings:
            raise BizError(code=Code.WORK_MONTH_WARNING_CONFIRM, msg=f"仍有 {warnings} 项警告异常，请确认后关闭")
        old = month.status
        await bump_month(
            month,
            db,
            actor,
            status=WorkMonthStatus.closed,
            closed_at=datetime.now(),
            closed_by=actor,
        )
        await log_month_status(month, from_status=old, action=WorkMonthAction.close, actor=actor, db=db, reason=payload.reason, summary=counts)
    return await summary(month_id)


async def reopen_month(month_id: int, revision: int, reason: str, actor: str) -> WorkMonthSummaryOut:
    async with in_transaction(get_db_conn(WorkMonth)) as db:
        month = await lock_month(month_id, db, writable=False)
        if month.revision != revision:
            raise BizError(code=Code.WORK_TICKET_REVISION_CONFLICT, msg="月度任务已被修改，请重新加载")
        if month.status not in (WorkMonthStatus.verified, WorkMonthStatus.closed):
            raise BizError(code=Code.WORK_MONTH_STATE_INVALID, msg="只有已核对或已关闭的月度任务可以重新打开")
        if not reason or not reason.strip():
            raise BizError(code=Code.REQUEST_VALIDATION, msg="重新打开必须填写原因")
        old = month.status
        await bump_month(
            month,
            db,
            actor,
            status=WorkMonthStatus.in_progress,
            closed_at=None,
            closed_by=None,
            reopened_at=datetime.now(),
            reopen_count=month.reopen_count + 1,
        )
        await log_month_status(month, from_status=old, action=WorkMonthAction.reopen, actor=actor, db=db, reason=reason)
    return await summary(month_id)


async def ensure_actor() -> str:
    return actor_name()
