"""Bounded multi-sheet Excel exports for a month and for report views."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from decimal import Decimal
from typing import Any

from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import TicketStatus, WorkTicket, WorkTicketAssignment, WorkTimeEntry
from app.business.work_ticket_management.schemas_workflow import ReconcileCategory, ReconcileSearchIn, ReportExportIn
from app.business.work_ticket_management.services import reports
from app.business.work_ticket_management.services.master_data import get_month_unit
from app.business.work_ticket_management.services.reconciliation import search as reconciliation_search
from app.utils import BizError, Code, get_db_conn, write_excel_sheets

MAX_EXPORT_ROWS = 10000


def _decimal(value: Decimal | None, places: int = 2) -> str:
    return "" if value is None else format(value, f".{places}f")


async def export_month_workbook(month_id: int) -> bytes:
    async with in_transaction(get_db_conn(WorkTicket)) as db:
        month, unit = await get_month_unit(month_id, db)
        tickets = list(await WorkTicket.filter(work_month_id=month_id, status=TicketStatus.active).using_db(db).order_by("id"))
        if len(tickets) > MAX_EXPORT_ROWS:
            raise BizError(code=Code.WORK_EXPORT_TOO_LARGE, msg=f"工票单表最多导出 {MAX_EXPORT_ROWS} 行，请缩小范围")
        ticket_ids = [ticket.id for ticket in tickets]
        assignments = list(await WorkTicketAssignment.filter(ticket_id__in=ticket_ids).using_db(db).prefetch_related("worker")) if ticket_ids else []
        assignment_count: dict[int, int] = defaultdict(int)
        worker_names: dict[int, list[str]] = defaultdict(list)
        for assignment in assignments:
            assignment_count[assignment.ticket_id] += 1
            if assignment.worker is not None:
                worker_names[assignment.ticket_id].append(assignment.worker.name)
        hours_by_ticket: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        entries = (
            list(await WorkTimeEntry.filter(assignment__ticket_id__in=ticket_ids).using_db(db).select_related("assignment__ticket__work_month", "assignment__worker").order_by("work_date", "id"))
            if ticket_ids
            else []
        )
        if len(entries) > MAX_EXPORT_ROWS:
            raise BizError(code=Code.WORK_EXPORT_TOO_LARGE, msg=f"工时明细最多导出 {MAX_EXPORT_ROWS} 行，请缩小范围")
        worker_tickets: dict[int, set[int]] = defaultdict(set)
        worker_hours: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        worker_names_by_id: dict[int, str] = {}
        worker_no_by_id: dict[int, str] = {}
        entry_rows: list[list[Any]] = []
        for entry in entries:
            assignment = entry.assignment
            ticket = assignment.ticket
            worker = assignment.worker
            ticket_month = ticket.work_month.year_month
            hours_by_ticket[ticket.id] += entry.hours
            worker_tickets[worker.id].add(ticket.id)
            worker_hours[worker.id] += entry.hours
            worker_names_by_id[worker.id] = worker.name
            worker_no_by_id[worker.id] = worker.worker_no or ""
            entry_rows.append([
                ticket.ticket_code or "",
                ticket.part_no_snapshot or "",
                worker.name,
                entry.work_date.isoformat(),
                entry.accounting_month or ticket_month,
                _decimal(entry.hours),
                entry.remark or "",
            ])
        ticket_rows = [
            [
                ticket.ticket_code or "",
                ticket.part_no_snapshot or "",
                ticket.order_no_snapshot or "",
                ticket.name_snapshot or "",
                ticket.status.value,
                ticket.reconcile_status.value,
                assignment_count.get(ticket.id, 0),
                ", ".join(worker_names.get(ticket.id, [])),
                _decimal(hours_by_ticket.get(ticket.id)),
                ticket.remark or "",
            ]
            for ticket in tickets
        ]
        worker_rows = [
            [
                worker_names_by_id[worker_id],
                worker_no_by_id[worker_id],
                unit.name,
                len(worker_tickets[worker_id]),
                _decimal(worker_hours[worker_id]),
            ]
            for worker_id in sorted(worker_names_by_id, key=lambda value: worker_names_by_id[value])
        ]
        if len(worker_rows) > MAX_EXPORT_ROWS:
            raise BizError(code=Code.WORK_EXPORT_TOO_LARGE, msg=f"人员统计最多导出 {MAX_EXPORT_ROWS} 行")
    anomaly_rows: list[list[Any]] = []
    for category in ReconcileCategory:
        first_total, first_items = await reconciliation_search(month_id, ReconcileSearchIn.model_validate({"category": category, "current": 1, "size": 1000}))
        if first_total > MAX_EXPORT_ROWS:
            raise BizError(code=Code.WORK_EXPORT_TOO_LARGE, msg=f"异常核对最多导出 {MAX_EXPORT_ROWS} 行")
        items = list(first_items)
        page = 2
        while len(items) < first_total:
            _, more = await reconciliation_search(month_id, ReconcileSearchIn.model_validate({"category": category, "current": page, "size": 1000}))
            items.extend(more)
            page += 1
        for item in items:
            anomaly_rows.append([category.value, item.severity, item.key, item.title, item.detail or ""])
    sheets = [
        ("工票汇总", ["工票码", "项目号", "订单号", "名称", "状态", "核对状态", "分配人数", "分配人员", "工时合计", "备注"], ticket_rows),
        ("工时明细", ["工票码", "项目号", "人员", "工作日期", "归属月份", "工时", "备注"], entry_rows),
        ("人员统计", ["人员", "人员编号", "生产单位", "工票数", "工时合计"], worker_rows),
        ("异常核对", ["分类", "级别", "稳定键", "标题", "说明"], anomaly_rows),
    ]
    return await asyncio.to_thread(write_excel_sheets, sheets)


async def export_report(payload: ReportExportIn) -> bytes:
    if payload.report_type == "monthly":
        data = await reports.monthly_report(payload)
        headers = ["月份", "生产单位", "工票数", "已分配", "未分配", "已登记工时", "未登记工时", "工时合计"]
        records = [
            [row.year_month, row.production_unit_name, row.ticket_count, row.assigned_count, row.unassigned_count, row.timed_count, row.no_time_count, _decimal(row.total_hours)] for row in data.rows
        ]
        title = "月度统计"
    elif payload.report_type == "worker_hours":
        data = await reports.worker_hours_report(payload)
        headers = ["人员", "生产单位", "工票数", "工时合计"]
        records = [[row.worker_name, row.production_unit_name or "", row.ticket_count, _decimal(row.hours)] for row in data.rows]
        title = "人员工时"
    elif payload.report_type == "worker_dates":
        data = await reports.worker_dates_report(payload)
        headers = ["工作日期", "人员", "工时"]
        records = [[row.work_date.isoformat(), row.worker_name, _decimal(row.hours)] for row in data.rows]
        title = "按日期工时"
    elif payload.report_type == "ticket_status":
        data = await reports.ticket_status_report(payload)
        headers = ["工票状态", "核对状态", "数量"]
        records = [[row.status.value, row.reconcile_status.value, row.count] for row in data.rows]
        title = "工票状态"
    else:
        if payload.work_month_id is None:
            raise BizError(code=Code.REQUEST_VALIDATION, msg="异常报表必须指定月度任务")
        data = await reports.anomaly_report(payload.work_month_id)
        headers = ["分类", "级别", "数量"]
        records = [[row.category.value, row.severity, row.count] for row in data.rows]
        title = "异常统计"
    if len(records) > MAX_EXPORT_ROWS:
        raise BizError(code=Code.WORK_EXPORT_TOO_LARGE, msg=f"报表最多导出 {MAX_EXPORT_ROWS} 行，请缩小范围")
    return await asyncio.to_thread(write_excel_sheets, [(title, headers, records)])
