"""Work ticket management acceptance tests against isolated in-memory SQLite."""

from __future__ import annotations

import io
import re
from datetime import date
from decimal import Decimal

import pytest
from openpyxl import load_workbook
from tortoise.context import tortoise_test_context

from app.business.order_management.models import Order
from app.business.work_ticket_management.models import MatchStatus, ProductionUnit, Worker, WorkMonth, WorkMonthStatus
from app.business.work_ticket_management.rules import OrderSnapshot, TicketCodeRule, normalize_part_no, register_rule
from app.business.work_ticket_management.schemas_workflow import (
    CodePasteIn,
    ImportRowIgnoreIn,
    ImportRowMatchIn,
    ImportRowSearchIn,
    ManualImportIn,
    MappingSearchIn,
    OcrCandidateIn,
    ReconcileCategory,
    ReconcileSearchIn,
    ReportFilter,
    TicketAssignIn,
    TicketCreateIn,
    TimeBatchSaveIn,
    TimeMatrixIn,
    WorkMonthCloseIn,
    WorkMonthOpenIn,
)
from app.business.work_ticket_management.services import export, imports, master_data, months, reconciliation, reports, tickets, timesheet
from app.core.ctx import CTX_USER_ID
from app.utils import BizError, decode_id, encode_id


@pytest.fixture
async def wt_db():
    async with tortoise_test_context(
        modules=["app.business.order_management.models", "app.business.work_ticket_management.models"],
        app_label="app_system",
        connection_label="conn_system",
        use_tz=False,
    ):
        token = CTX_USER_ID.set(1)
        yield
        CTX_USER_ID.reset(token)


async def setup_month(year_month: str = "2026-11") -> tuple[ProductionUnit, Worker, WorkMonth]:
    unit = await ProductionUnit.create(code="U1", name="一车间")
    worker = await Worker.create(name="张三", production_unit_id=unit.id)
    summary = await months.open_month(WorkMonthOpenIn(year_month=year_month, production_unit_id=encode_id(unit.id)), "tester")
    month = await WorkMonth.get(id=summary.id)
    return unit, worker, month


@pytest.mark.asyncio(loop_scope="session")
async def test_import_match_mapping_and_ticket_snapshots(wt_db):
    unit, worker, month = await setup_month()
    order = await Order.create(order_no="O-100201", part_no="100201", name="横梁", net_weight="1.500000", gross_weight="2.500000", process_route="焊接")
    other_unit = await ProductionUnit.create(code="U2", name="二车间")
    other_order = await Order.create(order_no="O-100202", part_no="100202", name="纵梁", net_weight="2.000000")
    await master_data.create_mapping_from_payload(other_order.id, other_unit.id, None, "tester")
    mapping_total, mapping_rows = await master_data.search_mappings(MappingSearchIn.model_validate({"keyword": "O-100202", "current": 1, "size": 10}))
    assert mapping_total == 1
    assert mapping_rows[0].order_no == "O-100202"
    assert mapping_rows[0].production_unit_name == "二车间"

    result = await imports.manual_import(
        ManualImportIn.model_validate(
            {
                "workMonthId": encode_id(month.id),
                "sourceType": "plan",
                "rows": [
                    {"rawPartNo": "100201"},
                    {"rawPartNo": "100202"},
                    {"rawPartNo": "100203"},
                ],
            }
        )
    )
    assert result.row_count == 3
    rows = await imports.list_rows(ImportRowSearchIn.model_validate({"workMonthId": encode_id(month.id), "current": 1, "size": 20}))
    by_part = {row.raw_part_no: row for row in rows[1]}
    assert by_part["100201"].match_status == MatchStatus.unassigned
    assert by_part["100202"].match_status == MatchStatus.other_unit
    assert by_part["100203"].match_status == MatchStatus.missing

    matched = await imports.match_row(by_part["100201"].id, ImportRowMatchIn.model_validate({"orderId": encode_id(order.id), "confirmMapping": True}))
    assert matched.match_status == MatchStatus.matched

    ticket = await tickets.create_ticket(
        TicketCreateIn.model_validate(
            {
                "workMonthId": encode_id(month.id),
                "orderId": encode_id(order.id),
                "sourceImportRowId": encode_id(matched.id),
                "ticketCode": "000123456",
                "workerIds": [encode_id(worker.id)],
            }
        )
    )
    assert ticket.ticket_code == "000123456"
    assert ticket.part_no_snapshot == "100201"
    assert ticket.worker_names == ["张三"]
    await Order.filter(id=order.id).update(name="新名称", part_no="999999")
    refreshed = await tickets.detail(ticket.id)
    assert refreshed.name_snapshot == "横梁"
    assert refreshed.part_no_snapshot == "100201"

    with pytest.raises(BizError, match="已存在"):
        await tickets.create_ticket(
            TicketCreateIn.model_validate(
                {
                    "workMonthId": encode_id(month.id),
                    "orderId": encode_id(order.id),
                    "ticketCode": "000123456",
                }
            )
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_assignment_time_matrix_revision_and_closed_month(wt_db):
    unit, worker, month = await setup_month()
    order = await Order.create(order_no="O-TIME", part_no="TIME-1", name="工时件", net_weight="1")
    await master_data.create_mapping_from_payload(order.id, unit.id, None, "tester")
    ticket = await tickets.create_ticket(TicketCreateIn.model_validate({"workMonthId": encode_id(month.id), "orderId": encode_id(order.id)}))
    ticket_id = ticket.id
    assigned = await tickets.assign_workers(ticket_id, TicketAssignIn.model_validate({"revision": ticket.revision, "workerIds": [encode_id(worker.id)]}))
    assert assigned.assignment_count == 1
    assert assigned.has_time is False

    saved = await timesheet.batch_save(
        TimeBatchSaveIn.model_validate(
            {
                "workMonthId": encode_id(month.id),
                "entries": [
                    {
                        "ticketId": encode_id(ticket_id),
                        "workerId": encode_id(worker.id),
                        "workDate": "2026-11-05",
                        "hours": "4.50",
                        "revision": assigned.revision,
                    }
                ],
            }
        )
    )
    assert saved.saved_count == 1
    assert saved.tickets[0].total_hours == Decimal("4.50")
    matrix = await timesheet.matrix(TimeMatrixIn.model_validate({"workMonthId": encode_id(month.id), "workerIds": [encode_id(worker.id)]}))
    assert len(matrix.entries) == 1
    assert matrix.total_hours == Decimal("4.50")

    with pytest.raises(BizError, match="其他操作"):
        await timesheet.batch_save(
            TimeBatchSaveIn.model_validate(
                {
                    "workMonthId": encode_id(month.id),
                    "entries": [
                        {
                            "ticketId": encode_id(ticket_id),
                            "workerId": encode_id(worker.id),
                            "workDate": "2026-11-06",
                            "hours": "2",
                            "revision": assigned.revision,
                        }
                    ],
                }
            )
        )

    summary = await months.verify_month(month.id, (await months.summary(month.id)).revision, None, "tester")
    assert summary.status == WorkMonthStatus.verified
    with pytest.raises(BizError, match="核对"):
        await tickets.create_ticket(TicketCreateIn.model_validate({"workMonthId": encode_id(month.id), "orderId": encode_id(order.id)}))
    with pytest.raises(BizError, match="核对"):
        await imports.manual_import(
            ManualImportIn.model_validate(
                {
                    "workMonthId": encode_id(month.id),
                    "sourceType": "plan",
                    "rows": [{"rawPartNo": "TIME-1"}],
                }
            )
        )
    reopened = await months.reopen_month(month.id, summary.revision, "补录工时", "tester")
    assert reopened.status == WorkMonthStatus.in_progress
    verified_again = await months.verify_month(month.id, reopened.revision, None, "tester")
    forced = await months.close_month(month.id, WorkMonthCloseIn.model_validate({"revision": verified_again.revision, "confirmWarnings": True}), "tester")
    assert forced.status == WorkMonthStatus.closed
    with pytest.raises(BizError, match="已核对或关闭"):
        await timesheet.batch_save(
            TimeBatchSaveIn.model_validate(
                {
                    "workMonthId": encode_id(month.id),
                    "entries": [
                        {
                            "ticketId": encode_id(ticket_id),
                            "workerId": encode_id(worker.id),
                            "workDate": "2026-11-07",
                            "hours": "1",
                            "revision": forced.revision,
                        }
                    ],
                }
            )
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_reconciliation_categories_and_code_ocr(wt_db):
    unit, worker, month = await setup_month()
    order = await Order.create(order_no="O-REC", part_no="REC-1", name="核对件", net_weight="1")
    await master_data.create_mapping_from_payload(order.id, unit.id, None, "tester")
    await imports.manual_import(
        ManualImportIn.model_validate(
            {
                "workMonthId": encode_id(month.id),
                "sourceType": "plan",
                "rows": [{"rawPartNo": "REC-1"}, {"rawPartNo": "REC-2"}],
            }
        )
    )
    await imports.manual_import(
        ManualImportIn.model_validate(
            {
                "workMonthId": encode_id(month.id),
                "sourceType": "actual",
                "rows": [{"rawPartNo": "REC-1"}, {"rawPartNo": "REC-3"}],
            }
        )
    )
    await tickets.create_ticket(TicketCreateIn.model_validate({"workMonthId": encode_id(month.id), "orderId": encode_id(order.id), "ticketCode": "000900001"}))
    summary = await reconciliation.summary(month.id)
    assert summary.counts[ReconcileCategory.plan_missing_actual.value] == 1
    assert summary.counts[ReconcileCategory.actual_missing_plan.value] == 1
    assert summary.counts[ReconcileCategory.unassigned.value] == 1
    total, items = await reconciliation.search(month.id, ReconcileSearchIn.model_validate({"category": "unassigned", "current": 1, "size": 10}))
    assert total == 1
    assert items[0].key.startswith("ticket:")

    unassigned_row = (await imports.list_rows(ImportRowSearchIn.model_validate({"workMonthId": encode_id(month.id), "sourceType": "actual", "current": 1, "size": 10})))[1]
    # The actual row REC-3 has no order; ignoring an ambiguous/missing row is persisted.
    await imports.ignore_row(unassigned_row[1].id, ImportRowIgnoreIn(reason="sample ignore"))
    after = await reconciliation.summary(month.id)
    assert after.counts[ReconcileCategory.actual_missing_plan.value] == 0

    candidates = await tickets.ocr_candidates(OcrCandidateIn.model_validate({"workMonthId": encode_id(month.id), "text": "OO0900001\n000900001"}))
    assert candidates[0].normalized == "000900001"
    assert candidates[0].duplicate is False
    assert candidates[1].duplicate is True

    # Paste a leading-zero code into a second ticket and export the month workbook.
    second = await tickets.create_ticket(TicketCreateIn.model_validate({"workMonthId": encode_id(month.id), "orderId": encode_id(order.id)}))
    pasted = await tickets.paste_codes(CodePasteIn.model_validate({"items": [{"ticketId": encode_id(second.id), "revision": second.revision, "code": "000900002"}]}))
    assert pasted.updated_count == 1
    content = await export.export_month_workbook(month.id)
    workbook = load_workbook(filename=io.BytesIO(content), read_only=True)
    assert {"工票汇总", "工时明细", "人员统计", "异常核对"} <= set(workbook.sheetnames)
    workbook.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_reports_use_persisted_records(wt_db):
    unit, worker, month = await setup_month()
    order = await Order.create(order_no="O-REP", part_no="REP-1", name="报表件", net_weight="1")
    await master_data.create_mapping_from_payload(order.id, unit.id, None, "tester")
    ticket = await tickets.create_ticket(TicketCreateIn.model_validate({"workMonthId": encode_id(month.id), "orderId": encode_id(order.id), "ticketCode": "000700001"}))
    await tickets.assign_workers(ticket.id, TicketAssignIn.model_validate({"revision": ticket.revision, "workerIds": [encode_id(worker.id)]}))
    current = await tickets.detail(ticket.id)
    await timesheet.batch_save(
        TimeBatchSaveIn.model_validate(
            {
                "workMonthId": encode_id(month.id),
                "entries": [{"ticketId": encode_id(ticket.id), "workerId": encode_id(worker.id), "workDate": "2026-11-08", "hours": "6.25", "revision": current.revision}],
            }
        )
    )
    monthly = await reports.monthly_report(ReportFilter.model_validate({}))
    assert monthly.rows[0].ticket_count == 1
    assert monthly.totals["totalHours"] == Decimal("6.25")
    workers = await reports.worker_hours_report(ReportFilter.model_validate({}))
    assert workers.rows[0].worker_name == "张三"
    assert workers.rows[0].hours == Decimal("6.25")
    dates = await reports.worker_dates_report(ReportFilter.model_validate({}))
    assert dates.rows[0].work_date == date(2026, 11, 8)
    status = await reports.ticket_status_report(ReportFilter.model_validate({}))
    assert status.rows[0].count == 1


def test_ticket_code_rule_samples_and_normalization():
    rule = TicketCodeRule(
        name="sample",
        version="1",
        description="sample only",
        pattern=re.compile(r"^\d{9}$"),
        transform=lambda order, sequence: f"{order.order_no.removeprefix('O-').zfill(9)}",
        samples=(("O-123456", "000123456"),),
    )
    register_rule(rule)
    assert rule.preview(OrderSnapshot(order_no="O-123456", part_no="P", name="N")) == "000123456"
    assert normalize_part_no(" １００２０１ ") == "100201"
