"""Persisted-data reports; all totals come from database records, never page data."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.business.work_ticket_management.models import (
    ReconcileStatus,
    TicketStatus,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.business.work_ticket_management.rules import month_of_date
from app.business.work_ticket_management.schemas_workflow import (
    AnomalyReportOut,
    AnomalyReportRow,
    MonthlyTicketReportRow,
    MonthReportOut,
    ReconcileCategory,
    ReportBasis,
    ReportFilter,
    TicketStatusReportOut,
    TicketStatusReportRow,
    WorkerDatesReportOut,
    WorkerHoursByDateRow,
    WorkerHoursReportOut,
    WorkerHoursReportRow,
)
from app.business.work_ticket_management.services.common import sqid
from app.business.work_ticket_management.services.reconciliation import summary as reconciliation_summary


def _in_range(month: str, start: str | None, end: str | None) -> bool:
    return (start is None or month >= start) and (end is None or month <= end)


async def _tickets(filters: ReportFilter) -> list[WorkTicket]:
    query = WorkTicket.all()
    if not filters.include_void:
        query = query.filter(status=TicketStatus.active)
    if filters.production_unit_id is not None:
        query = query.filter(work_month__production_unit_id=filters.production_unit_id)
    if filters.year_month_start:
        query = query.filter(work_month__year_month__gte=filters.year_month_start)
    if filters.year_month_end:
        query = query.filter(work_month__year_month__lte=filters.year_month_end)
    return list(await query.select_related("work_month__production_unit"))


async def monthly_report(filters: ReportFilter) -> MonthReportOut:
    tickets = await _tickets(filters)
    ticket_ids = [ticket.id for ticket in tickets]
    assigned: set[int] = set()
    if ticket_ids:
        assigned = {row["ticket_id"] for row in await WorkTicketAssignment.filter(ticket_id__in=ticket_ids).values("ticket_id")}
    hours_by_ticket: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
    if ticket_ids:
        for row in await WorkTimeEntry.filter(assignment__ticket_id__in=ticket_ids).values("assignment__ticket_id", "hours"):
            hours_by_ticket[row["assignment__ticket_id"]] += Decimal(row["hours"])
    groups: dict[tuple[str, int], list[WorkTicket]] = defaultdict(list)
    for ticket in tickets:
        groups[(ticket.work_month.year_month, ticket.work_month.production_unit_id)].append(ticket)
    rows: list[MonthlyTicketReportRow] = []
    for (year_month, production_unit_id), group_tickets in sorted(groups.items()):
        unit = group_tickets[0].work_month.production_unit
        assigned_count = sum(1 for ticket in group_tickets if ticket.id in assigned)
        timed_count = sum(1 for ticket in group_tickets if ticket.id in hours_by_ticket)
        total_hours = sum((hours_by_ticket.get(ticket.id, Decimal("0.00")) for ticket in group_tickets), Decimal("0.00"))
        rows.append(
            MonthlyTicketReportRow(
                year_month=year_month,
                production_unit_id=sqid(production_unit_id),
                production_unit_name=unit.name if unit is not None else "",
                ticket_count=len(group_tickets),
                assigned_count=assigned_count,
                unassigned_count=len(group_tickets) - assigned_count,
                timed_count=timed_count,
                no_time_count=len(group_tickets) - timed_count,
                total_hours=total_hours.quantize(Decimal("0.01")),
            )
        )
    totals = {
        "ticketCount": sum(row.ticket_count for row in rows),
        "assignedCount": sum(row.assigned_count for row in rows),
        "unassignedCount": sum(row.unassigned_count for row in rows),
        "timedCount": sum(row.timed_count for row in rows),
        "noTimeCount": sum(row.no_time_count for row in rows),
        "totalHours": sum((row.total_hours for row in rows), Decimal("0.00")).quantize(Decimal("0.01")),
    }
    return MonthReportOut(rows=rows, totals=totals)


def _entry_month(entry: WorkTimeEntry, basis: ReportBasis) -> str:
    ticket_month = entry.assignment.ticket.work_month.year_month
    if basis == ReportBasis.work_date:
        return month_of_date(entry.work_date)
    if basis == ReportBasis.accounting_month:
        return entry.accounting_month or ticket_month
    return ticket_month


async def _entries(filters: ReportFilter) -> list[WorkTimeEntry]:
    query = WorkTimeEntry.all()
    if filters.worker_id is not None:
        query = query.filter(assignment__worker_id=filters.worker_id)
    if filters.production_unit_id is not None:
        query = query.filter(assignment__ticket__work_month__production_unit_id=filters.production_unit_id)
    if not filters.include_void:
        query = query.filter(assignment__ticket__status=TicketStatus.active)
    if filters.basis == ReportBasis.ticket_month:
        if filters.year_month_start:
            query = query.filter(assignment__ticket__work_month__year_month__gte=filters.year_month_start)
        if filters.year_month_end:
            query = query.filter(assignment__ticket__work_month__year_month__lte=filters.year_month_end)
    entries = list(await query.select_related("assignment__ticket__work_month__production_unit", "assignment__worker"))
    if filters.basis != ReportBasis.ticket_month:
        entries = [entry for entry in entries if _in_range(_entry_month(entry, filters.basis), filters.year_month_start, filters.year_month_end)]
    return entries


async def worker_hours_report(filters: ReportFilter) -> WorkerHoursReportOut:
    entries = await _entries(filters)
    meta: dict[int, tuple[str, int | None, str | None]] = {}
    tickets_by_worker: dict[int, set[int]] = defaultdict(set)
    hours_by_worker: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for entry in entries:
        worker = entry.assignment.worker
        ticket = entry.assignment.ticket
        unit = ticket.work_month.production_unit
        meta[worker.id] = (worker.name, unit.id if unit is not None else None, unit.name if unit is not None else None)
        tickets_by_worker[worker.id].add(ticket.id)
        hours_by_worker[worker.id] += entry.hours
    rows = [
        WorkerHoursReportRow(
            worker_id=sqid(worker_id),
            worker_name=name,
            production_unit_id=sqid(unit_id),
            production_unit_name=unit_name,
            ticket_count=len(tickets_by_worker[worker_id]),
            hours=hours_by_worker[worker_id].quantize(Decimal("0.01")),
        )
        for worker_id, (name, unit_id, unit_name) in sorted(meta.items(), key=lambda item: item[1][0])
    ]
    totals = {"workers": len(rows), "tickets": sum(row.ticket_count for row in rows), "hours": sum((row.hours for row in rows), Decimal("0.00")).quantize(Decimal("0.01"))}
    return WorkerHoursReportOut(rows=rows, totals=totals)


async def worker_dates_report(filters: ReportFilter) -> WorkerDatesReportOut:
    entries = await _entries(filters)
    groups: dict[tuple[date, int], Decimal] = defaultdict(lambda: Decimal("0.00"))
    names: dict[int, str] = {}
    for entry in entries:
        worker = entry.assignment.worker
        names[worker.id] = worker.name
        groups[(entry.work_date, worker.id)] += entry.hours
    rows = [
        WorkerHoursByDateRow(work_date=work_date, worker_id=sqid(worker_id), worker_name=names[worker_id], hours=hours.quantize(Decimal("0.01")))
        for (work_date, worker_id), hours in sorted(groups.items())
    ]
    return WorkerDatesReportOut(rows=rows)


async def ticket_status_report(filters: ReportFilter) -> TicketStatusReportOut:
    tickets = await _tickets(filters)
    groups: dict[tuple[TicketStatus, ReconcileStatus], int] = defaultdict(int)
    for ticket in tickets:
        groups[(ticket.status, ticket.reconcile_status)] += 1
    ordered = sorted(groups.items(), key=lambda item: (item[0][0].value, item[0][1].value))
    return TicketStatusReportOut(rows=[TicketStatusReportRow(status=status, reconcile_status=reconcile, count=count) for (status, reconcile), count in ordered])


async def anomaly_report(month_id: int) -> AnomalyReportOut:
    summary = await reconciliation_summary(month_id)
    rows = []
    for category in ReconcileCategory:
        count = summary.counts.get(category.value, 0)
        severity = "blocking" if category.value in {"ticket_without_order", "duplicate_code"} else "warning"
        rows.append(AnomalyReportRow(category=category, severity=severity, count=count))
    totals = {"blocking": summary.blocking, "warnings": summary.warnings}
    return AnomalyReportOut(rows=rows, totals=totals)
