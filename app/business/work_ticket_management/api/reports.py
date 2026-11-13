"""Persisted-data report endpoints."""

from fastapi import APIRouter

from app.business.work_ticket_management import constants
from app.business.work_ticket_management.api.common import dump, excel_file
from app.business.work_ticket_management.schemas_workflow import AnomalyReportIn, ReportExportIn, ReportFilter
from app.business.work_ticket_management.services import export, reports
from app.utils import Success, require_buttons

router = APIRouter()


@router.post("/reports/monthly", summary="月度工票统计", name="work_ticket_management.reports.monthly")
async def monthly(obj_in: ReportFilter) -> Success:
    return Success(data=dump(await reports.monthly_report(obj_in)))


@router.post("/reports/worker-hours", summary="人员工时统计", name="work_ticket_management.reports.worker_hours")
async def worker_hours(obj_in: ReportFilter) -> Success:
    return Success(data=dump(await reports.worker_hours_report(obj_in)))


@router.post("/reports/worker-dates", summary="按日期人员工时", name="work_ticket_management.reports.worker_dates")
async def worker_dates(obj_in: ReportFilter) -> Success:
    return Success(data=dump(await reports.worker_dates_report(obj_in)))


@router.post("/reports/ticket-status", summary="工票状态统计", name="work_ticket_management.reports.ticket_status")
async def ticket_status(obj_in: ReportFilter) -> Success:
    return Success(data=dump(await reports.ticket_status_report(obj_in)))


@router.post("/reports/anomalies", summary="异常统计", name="work_ticket_management.reports.anomalies")
async def anomalies(obj_in: AnomalyReportIn) -> Success:
    return Success(data=dump(await reports.anomaly_report(obj_in.work_month_id)))


@router.post("/reports/export", summary="导出统计报表", name="work_ticket_management.reports.export", dependencies=[require_buttons(constants.B_REPORT_EXPORT)])
async def export_report(obj_in: ReportExportIn) -> Success:
    content = await export.export_report(obj_in)
    return excel_file(f"{obj_in.report_type}.xlsx", content)
