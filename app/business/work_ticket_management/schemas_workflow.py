# pyright: reportIncompatibleVariableOverride=false
"""工票工时管理 — 聚合业务请求/响应 Schema。

生成的 ``schemas.py`` 只承载简单 CRUD；本文件承载月度、导入、匹配、工票、
工时、核对和报表等聚合流程。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from app.business.work_ticket_management.models import (
    AssignmentSource,
    HandlingStatus,
    ImportSourceType,
    MatchStatus,
    ReconcileStatus,
    TicketCodeSource,
    TicketStatus,
    WorkMonthStatus,
)
from app.utils import PageQueryBase, SchemaBase, SqidId, StrEnum

YearMonth = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", title="月份 YYYY-MM")]
PartNoText = Annotated[str, Field(min_length=1, max_length=200)]
TicketCodeText = Annotated[str, Field(min_length=1, max_length=100)]
RemarkText = Annotated[str, Field(min_length=1, max_length=500)]


# ============================================================
# 基础资料与订单候选
# ============================================================


class UnitOption(SchemaBase):
    id: SqidId
    code: str
    name: str


class WorkerOption(SchemaBase):
    id: SqidId
    worker_no: str | None
    name: str
    production_unit_id: SqidId | None
    enabled: bool


class OrderCandidateQuery(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    part_no: PartNoText
    limit: int = Field(20, ge=1, le=50)
    include_other_units: bool = False
    include_partial: bool = False


class OrderCandidateOut(SchemaBase):
    id: SqidId
    order_no: str
    part_no: str
    name: str
    net_weight: Decimal
    gross_weight: Decimal | None
    process_route: str | None
    quantity: int | None
    received_quantity: int | None
    mapping_status: Literal["confirmed", "other_unit", "unconfirmed"]
    mapped_units: list[str] = Field(default_factory=list)


# ============================================================
# 月度任务
# ============================================================


class WorkMonthOpenIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    year_month: YearMonth
    production_unit_id: SqidId


class WorkMonthActionIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    reason: RemarkText | None = None


class WorkMonthCloseIn(WorkMonthActionIn):
    confirm_warnings: bool = False


class WorkMonthSummaryOut(SchemaBase):
    id: SqidId
    year_month: str
    production_unit_id: SqidId
    production_unit_name: str
    status: WorkMonthStatus
    revision: int
    row_count: int = 0
    matched_rows: int = 0
    ambiguous_rows: int = 0
    ticket_count: int = 0
    assigned_ticket_count: int = 0
    timed_ticket_count: int = 0
    anomaly_count: int = 0
    has_actual_batch: bool = False
    closed_at: datetime | None = None


class WorkMonthStatusLogOut(SchemaBase):
    id: SqidId
    from_status: WorkMonthStatus | None
    to_status: WorkMonthStatus
    action: str
    reason: str | None
    created_by: str | None
    created_at: datetime


# ============================================================
# 导入与匹配
# ============================================================


class ImportPreviewRow(SchemaBase):
    row_number: int
    raw_part_no: str
    normalized_part_no: str
    match_status: MatchStatus
    match_source: str
    order_id: SqidId | None = None
    order_no: str | None = None
    part_no: str | None = None
    name: str | None = None
    candidate_count: int = 0
    duplicate_of_row_id: SqidId | None = None
    note: str | None = None


class ImportPreviewOut(SchemaBase):
    source_type: ImportSourceType
    rows: list[ImportPreviewRow]
    errors: list[str] = Field(default_factory=list)
    total_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    matched_rows: int = 0
    ambiguous_rows: int = 0
    missing_rows: int = 0
    truncated: bool = False


class ImportCommitOut(SchemaBase):
    batch_id: SqidId
    row_count: int
    invalid_rows: int = 0
    duplicate_rows: int = 0
    matched_rows: int = 0
    ambiguous_rows: int = 0
    missing_rows: int = 0


class ManualImportRowIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    raw_part_no: PartNoText
    source_quantity: Decimal | None = Field(None, max_digits=16, decimal_places=3)


class ManualImportIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    source_type: ImportSourceType
    source_name: str | None = Field(None, max_length=255)
    rows: list[ManualImportRowIn] = Field(min_length=1, max_length=10000)


class ImportRowSearchIn(PageQueryBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId | None = None
    source_type: ImportSourceType | None = None
    match_status: MatchStatus | None = None
    handling_status: HandlingStatus | None = None
    batch_id: SqidId | None = None
    keyword: str | None = Field(None, max_length=200)


class ImportRowMatchIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    order_id: SqidId
    confirm_mapping: bool = True


class ImportRowIgnoreIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    reason: RemarkText


class ImportRowUpdateIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    raw_part_no: PartNoText | None = None
    source_quantity: Decimal | None = Field(None, max_digits=16, decimal_places=3)
    note: str | None = Field(None, max_length=500)


class ImportBatchVoidIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    reason: RemarkText


class ImportRowBatchMatchIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    ids: list[SqidId] | None = Field(None, min_length=1, max_length=10000)


class ImportRowOut(SchemaBase):
    id: SqidId
    batch_id: SqidId
    source_type: ImportSourceType
    row_number: int
    raw_part_no: str
    normalized_part_no: str
    order_id: SqidId | None
    order_no: str | None
    part_no: str | None
    name: str | None
    match_status: MatchStatus
    match_source: str
    handling_status: HandlingStatus
    handling_note: str | None
    duplicate_of_row_id: SqidId | None
    source_quantity: Decimal | None
    note: str | None


# ============================================================
# 工票
# ============================================================


class TicketCreateIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    order_id: SqidId | None = None
    source_import_row_id: SqidId | None = None
    part_no_snapshot: str | None = Field(None, max_length=200)
    name_snapshot: str | None = Field(None, max_length=200)
    ticket_code: str | None = Field(None, max_length=100)
    code_source: TicketCodeSource = TicketCodeSource.manual
    code_confidence: Decimal | None = Field(None, ge=0, le=1, max_digits=5, decimal_places=4)
    remark: str | None = Field(None, max_length=500)
    worker_ids: list[SqidId] = Field(default_factory=list, max_length=200)
    allow_disabled_workers: bool = False
    allow_add_mapping: bool = False


class TicketUpdateIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    order_id: SqidId | None = None
    ticket_code: str | None = Field(None, max_length=100)
    code_source: TicketCodeSource | None = None
    remark: str | None = Field(None, max_length=500)
    reconcile_status: ReconcileStatus | None = None
    reconcile_note: str | None = Field(None, max_length=500)
    allow_add_mapping: bool = False


class TicketVoidIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    reason: RemarkText


class TicketAssignIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    worker_ids: list[SqidId] = Field(min_length=1, max_length=200)
    allow_disabled: bool = False
    source: AssignmentSource = AssignmentSource.manual


class TicketBatchAssignIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    ticket_ids: list[SqidId] = Field(min_length=1, max_length=500)
    worker_ids: list[SqidId] = Field(min_length=1, max_length=200)
    allow_disabled: bool = False


class TicketUnassignIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    worker_id: SqidId


class TicketReconcileIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    status: Literal[ReconcileStatus.checked, ReconcileStatus.ignored]
    note: str | None = Field(None, max_length=500)


class CodePreviewItem(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    order_id: SqidId | None = None
    source_import_row_id: SqidId | None = None
    sequence: int = Field(1, ge=1, le=9999)


class CodePreviewIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    rule_name: str | None = Field(None, max_length=50)
    items: list[CodePreviewItem] = Field(min_length=1, max_length=500)


class CodePreviewRow(SchemaBase):
    order_id: SqidId | None
    source_import_row_id: SqidId | None
    order_no: str | None
    part_no: str | None
    name: str | None
    preview_code: str | None
    valid: bool
    error: str | None
    conflict_ticket_id: SqidId | None
    conflict_code: str | None


class CodePreviewOut(SchemaBase):
    configured: bool
    rule_name: str | None
    rows: list[CodePreviewRow]
    conflicts: int = 0


class CodeConfirmItem(CodePreviewItem):
    code: str | None = Field(None, max_length=100)


class CodeConfirmIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    rule_name: str | None = Field(None, max_length=50)
    items: list[CodeConfirmItem] = Field(min_length=1, max_length=500)
    allow_add_mapping: bool = False


class CodeConfirmOut(SchemaBase):
    created_count: int
    skipped_count: int
    ticket_ids: list[SqidId]
    conflicts: list[str] = Field(default_factory=list)


class CodePasteItem(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    ticket_id: SqidId
    revision: int = Field(ge=1, le=2147483646)
    code: str = Field(min_length=1, max_length=100)


class CodePasteIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    items: list[CodePasteItem] = Field(min_length=1, max_length=500)


class CodePasteOut(SchemaBase):
    updated_count: int
    conflicts: list[str] = Field(default_factory=list)


class CodeLookupIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    codes: list[str] = Field(min_length=1, max_length=500)
    include_other_months: bool = True


class CodeLookupOut(SchemaBase):
    code: str
    normalized: str
    valid: bool
    ticket_id: SqidId | None = None
    ticket_code: str | None = None
    part_no: str | None = None
    order_no: str | None = None
    ticket_status: TicketStatus | None = None
    work_month_id: SqidId | None = None
    year_month: str | None = None
    work_month_status: WorkMonthStatus | None = None
    other_month_matches: list[dict] = Field(default_factory=list)


class OcrCandidateIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    text: str = Field(min_length=1, max_length=10000)
    numeric_mode: bool = True
    min_confidence: Decimal = Field(Decimal("0.9"), ge=0, le=1)


class OcrCandidateOut(SchemaBase):
    original: str
    normalized: str
    confidence: Decimal | None
    valid: bool
    duplicate: bool
    match: CodeLookupOut | None = None


class TicketAssignmentOut(SchemaBase):
    id: SqidId
    worker_id: SqidId
    worker_no: str | None
    worker_name: str
    worker_enabled: bool
    source: AssignmentSource
    remark: str | None


class TicketTimeEntryOut(SchemaBase):
    id: SqidId
    worker_id: SqidId
    worker_name: str
    work_date: date
    accounting_month: str | None
    hours: Decimal
    remark: str | None


class TicketSearchIn(PageQueryBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId | None = None
    production_unit_id: SqidId | None = None
    year_month_start: YearMonth | None = None
    year_month_end: YearMonth | None = None
    status: TicketStatus | None = None
    reconcile_status: ReconcileStatus | None = None
    assignment_status: Literal["all", "assigned", "unassigned"] = "all"
    time_status: Literal["all", "logged", "none"] = "all"
    keyword: str | None = Field(None, max_length=200)
    order_no: str | None = Field(None, max_length=100)
    part_no: str | None = Field(None, max_length=200)
    ticket_code: str | None = Field(None, max_length=100)


class TicketOut(SchemaBase):
    id: SqidId
    work_month_id: SqidId
    year_month: str
    production_unit_id: SqidId
    production_unit_name: str
    order_id: SqidId | None
    order_no_snapshot: str | None
    part_no_snapshot: str | None
    name_snapshot: str | None
    ticket_code: str | None
    code_source: TicketCodeSource
    code_confidence: Decimal | None
    status: TicketStatus
    reconcile_status: ReconcileStatus
    reconcile_note: str | None
    assignment_count: int = 0
    worker_names: list[str] = Field(default_factory=list)
    total_hours: Decimal = Decimal("0.00")
    has_time: bool = False
    revision: int
    remark: str | None
    created_at: datetime | None
    updated_at: datetime | None


class TicketDetailOut(TicketOut):
    assignments: list[TicketAssignmentOut] = Field(default_factory=list)
    time_entries: list[TicketTimeEntryOut] = Field(default_factory=list)


# ============================================================
# 工时
# ============================================================


class TimeMatrixIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    worker_ids: list[SqidId] | None = Field(None, max_length=50)
    ticket_ids: list[SqidId] | None = Field(None, max_length=200)
    work_date_start: date | None = None
    work_date_end: date | None = None
    ticket_limit: int = Field(100, ge=1, le=200)


class TimeMatrixTicket(SchemaBase):
    id: SqidId
    ticket_code: str | None
    part_no_snapshot: str | None
    order_no_snapshot: str | None
    name_snapshot: str | None
    revision: int


class TimeMatrixEntry(SchemaBase):
    id: SqidId
    ticket_id: SqidId
    worker_id: SqidId
    work_date: date
    accounting_month: str | None
    hours: Decimal


class TimeMatrixOut(SchemaBase):
    tickets: list[TimeMatrixTicket]
    workers: list[WorkerOption]
    entries: list[TimeMatrixEntry]
    total_hours: Decimal
    truncated: bool = False


class TimeBatchEntryIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    ticket_id: SqidId
    worker_id: SqidId
    work_date: date
    hours: Decimal | None = Field(None, gt=0, le=24, max_digits=5, decimal_places=2)
    entry_id: SqidId | None = None
    accounting_month: YearMonth | None = None
    revision: int = Field(ge=1, le=2147483646)


class TimeBatchSaveIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId
    entries: list[TimeBatchEntryIn] = Field(min_length=1, max_length=5000)


class TimeBatchTicketResult(SchemaBase):
    ticket_id: SqidId
    revision: int
    total_hours: Decimal


class TimeBatchSaveOut(SchemaBase):
    saved_count: int
    deleted_count: int
    tickets: list[TimeBatchTicketResult]


class TimeEntrySearchIn(PageQueryBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId | None = None
    production_unit_id: SqidId | None = None
    worker_id: SqidId | None = None
    ticket_id: SqidId | None = None
    work_date_start: date | None = None
    work_date_end: date | None = None
    accounting_month: YearMonth | None = None


class TimeEntryUpdateIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)
    hours: Decimal = Field(gt=0, le=24, max_digits=5, decimal_places=2)
    work_date: date
    accounting_month: YearMonth | None = None
    remark: str | None = Field(None, max_length=500)


class TimeEntryDeleteIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646)


class TimeEntryOut(SchemaBase):
    id: SqidId
    ticket_id: SqidId
    ticket_code: str | None
    part_no_snapshot: str | None
    order_no_snapshot: str | None
    worker_id: SqidId
    worker_name: str
    work_date: date
    accounting_month: str | None
    effective_month: str
    hours: Decimal
    remark: str | None
    revision: int


# ============================================================
# 核对与报表
# ============================================================


class ReconcileCategory(StrEnum):
    plan_missing_actual = "plan_missing_actual"
    actual_missing_plan = "actual_missing_plan"
    actual_without_ticket = "actual_without_ticket"
    ticket_without_order = "ticket_without_order"
    duplicate_code = "duplicate_code"
    unassigned = "unassigned"
    no_time = "no_time"
    ambiguous = "ambiguous"
    cross_month_duplicate = "cross_month_duplicate"


class ReconcileSummaryOut(SchemaBase):
    work_month_id: SqidId
    status: WorkMonthStatus
    counts: dict[str, int]
    blocking: int = 0
    warnings: int = 0
    has_actual_batch: bool = False


class ReconcileSearchIn(PageQueryBase):
    model_config = ConfigDict(extra="forbid")
    category: ReconcileCategory
    keyword: str | None = Field(None, max_length=200)


class ReconcileItemOut(SchemaBase):
    key: str
    category: ReconcileCategory
    severity: Literal["blocking", "warning"]
    entity_type: str
    entity_id: str | None
    title: str
    detail: str | None = None
    actions: list[str] = Field(default_factory=list)


class ReportBasis(StrEnum):
    ticket_month = "ticket_month"
    work_date = "work_date"
    accounting_month = "accounting_month"


class ReportFilter(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    year_month_start: YearMonth | None = None
    year_month_end: YearMonth | None = None
    production_unit_id: SqidId | None = None
    worker_id: SqidId | None = None
    include_void: bool = False
    basis: ReportBasis = ReportBasis.ticket_month


class MonthlyTicketReportRow(SchemaBase):
    year_month: str
    production_unit_id: SqidId
    production_unit_name: str
    ticket_count: int
    assigned_count: int
    unassigned_count: int
    timed_count: int
    no_time_count: int
    total_hours: Decimal


class WorkerHoursReportRow(SchemaBase):
    worker_id: SqidId
    worker_name: str
    production_unit_id: SqidId | None
    production_unit_name: str | None
    ticket_count: int
    hours: Decimal


class WorkerHoursByDateRow(SchemaBase):
    work_date: date
    worker_id: SqidId
    worker_name: str
    hours: Decimal


class TicketStatusReportRow(SchemaBase):
    status: TicketStatus
    reconcile_status: ReconcileStatus
    count: int


class AnomalyReportRow(SchemaBase):
    category: ReconcileCategory
    severity: Literal["blocking", "warning"]
    count: int


class AnomalyReportIn(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    work_month_id: SqidId


class ReportExportIn(ReportFilter):
    report_type: Literal["monthly", "worker_hours", "worker_dates", "ticket_status", "anomalies"]
    work_month_id: SqidId | None = None


class MonthReportOut(SchemaBase):
    rows: list[MonthlyTicketReportRow]
    totals: dict[str, Decimal | int]


class WorkerHoursReportOut(SchemaBase):
    rows: list[WorkerHoursReportRow]
    totals: dict[str, Decimal | int]


class WorkerDatesReportOut(SchemaBase):
    rows: list[WorkerHoursByDateRow]


class TicketStatusReportOut(SchemaBase):
    rows: list[TicketStatusReportRow]


class AnomalyReportOut(SchemaBase):
    rows: list[AnomalyReportRow]
    totals: dict[str, int]
