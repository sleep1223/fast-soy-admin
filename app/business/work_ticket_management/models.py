"""历史迁移引用的枚举，保留以支持数据库从头迁移。"""

from __future__ import annotations

from app.utils import StrEnum


class WorkMonthStatus(StrEnum):
    draft = "draft"
    in_progress = "in_progress"
    verified = "verified"
    closed = "closed"


class ImportSourceType(StrEnum):
    plan = "plan"
    actual = "actual"


class ImportBatchStatus(StrEnum):
    active = "active"
    void = "void"


class MatchStatus(StrEnum):
    pending = "pending"
    matched = "matched"
    ambiguous = "ambiguous"
    missing = "missing"
    unassigned = "unassigned"
    other_unit = "other_unit"
    invalid = "invalid"


class MatchSource(StrEnum):
    none = "none"
    auto = "auto"
    manual = "manual"


class HandlingStatus(StrEnum):
    open = "open"
    resolved = "resolved"
    ignored = "ignored"


class TicketCodeSource(StrEnum):
    none = "none"
    auto = "auto"
    manual = "manual"
    ocr = "ocr"


class TicketStatus(StrEnum):
    active = "active"
    void = "void"


class ReconcileStatus(StrEnum):
    pending = "pending"
    checked = "checked"
    ignored = "ignored"


class AssignmentSource(StrEnum):
    manual = "manual"
    batch = "batch"
    time_entry = "time_entry"


class WorkMonthAction(StrEnum):
    open = "open"
    start = "start"
    verify = "verify"
    close = "close"
    reopen = "reopen"
