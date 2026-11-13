# pyright: reportIncompatibleVariableOverride=false
"""工票工时管理 — 业务模型定义。"""

from __future__ import annotations

from tortoise import fields

from app.utils import AuditMixin, BaseModel, StrEnum


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


class ProductionUnit(BaseModel, AuditMixin):
    """生产单位"""

    id = fields.IntField(primary_key=True)
    code = fields.CharField(max_length=50, unique=True, description="单位编码")
    name = fields.CharField(max_length=100, db_index=True, description="单位名称")
    enabled = fields.BooleanField(default=True, description="是否启用")
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_production_unit"
        table_description = "生产单位"


class Worker(BaseModel, AuditMixin):
    """生产人员"""

    id = fields.IntField(primary_key=True)
    worker_no = fields.CharField(max_length=50, unique=True, null=True, description="人员编号")
    name = fields.CharField(max_length=100, db_index=True, description="姓名")
    production_unit_id: int | None
    production_unit = fields.ForeignKeyField(
        "app_system.ProductionUnit",
        null=True,
        related_name="workers",
        on_delete=fields.SET_NULL,
        db_index=True,
        description="默认所属生产单位",
    )
    enabled = fields.BooleanField(default=True, description="是否在用")
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_worker"
        table_description = "生产人员"


class OrderUnitMapping(BaseModel, AuditMixin):
    """订单与生产单位关系"""

    id = fields.IntField(primary_key=True)
    order_id: int
    order = fields.ForeignKeyField(
        "app_system.Order",
        related_name="work_ticket_unit_mappings",
        on_delete=fields.CASCADE,
        description="订单",
    )
    production_unit_id: int
    production_unit = fields.ForeignKeyField(
        "app_system.ProductionUnit",
        related_name="order_mappings",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="生产单位",
    )
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_order_unit_mapping"
        table_description = "订单与生产单位关系"
        unique_together = (("order", "production_unit"),)


class WorkMonth(BaseModel, AuditMixin):
    """月度任务"""

    id = fields.IntField(primary_key=True)
    year_month = fields.CharField(max_length=7, db_index=True, description="归属月份 YYYY-MM")
    production_unit_id: int
    production_unit = fields.ForeignKeyField(
        "app_system.ProductionUnit",
        related_name="work_months",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="生产单位",
    )
    status = fields.CharEnumField(
        enum_type=WorkMonthStatus,
        max_length=20,
        default=WorkMonthStatus.draft,
        db_index=True,
        description="状态",
    )
    remark = fields.CharField(max_length=500, null=True, description="备注")
    revision = fields.IntField(default=1, description="修订版本")
    closed_at = fields.DatetimeField(null=True, description="关闭时间")
    closed_by = fields.CharField(max_length=64, null=True, description="关闭人")
    reopened_at = fields.DatetimeField(null=True, description="最近重开时间")
    reopen_count = fields.IntField(default=0, description="重开次数")

    class Meta:
        table = "biz_work_ticket_management_work_month"
        table_description = "月度任务"
        unique_together = (("year_month", "production_unit"),)


class MonthlyImportBatch(BaseModel, AuditMixin):
    """月度导入批次"""

    id = fields.IntField(primary_key=True)
    work_month_id: int
    work_month = fields.ForeignKeyField(
        "app_system.WorkMonth",
        related_name="import_batches",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="月度任务",
    )
    source_type = fields.CharEnumField(
        enum_type=ImportSourceType,
        max_length=10,
        db_index=True,
        description="来源类型",
    )
    status = fields.CharEnumField(
        enum_type=ImportBatchStatus,
        max_length=10,
        default=ImportBatchStatus.active,
        db_index=True,
        description="批次状态",
    )
    source_name = fields.CharField(max_length=255, null=True, description="来源文件名或说明")
    content_hash = fields.CharField(max_length=64, null=True, db_index=True, description="文件内容 SHA-256")
    row_count = fields.IntField(default=0, description="来源数据行数")
    void_reason = fields.CharField(max_length=500, null=True, description="作废原因")
    voided_at = fields.DatetimeField(null=True, description="作废时间")
    voided_by = fields.CharField(max_length=64, null=True, description="作废人")
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_monthly_import_batch"
        table_description = "月度导入批次"


class MonthlyImportRow(BaseModel, AuditMixin):
    """导入原始明细"""

    id = fields.IntField(primary_key=True)
    batch_id: int
    batch = fields.ForeignKeyField(
        "app_system.MonthlyImportBatch",
        related_name="rows",
        on_delete=fields.RESTRICT,
        description="导入批次",
    )
    row_number = fields.IntField(description="源文件行号")
    raw_part_no = fields.CharField(max_length=200, description="原始项目号")
    normalized_part_no = fields.CharField(max_length=200, db_index=True, description="规范化项目号")
    order_id: int | None
    order = fields.ForeignKeyField(
        "app_system.Order",
        null=True,
        related_name="work_ticket_import_rows",
        on_delete=fields.SET_NULL,
        db_index=True,
        description="匹配订单",
    )
    match_status = fields.CharEnumField(
        enum_type=MatchStatus,
        max_length=20,
        default=MatchStatus.pending,
        db_index=True,
        description="订单匹配状态",
    )
    match_source = fields.CharEnumField(
        enum_type=MatchSource,
        max_length=10,
        default=MatchSource.none,
        description="匹配方式",
    )
    source_quantity = fields.DecimalField(max_digits=16, decimal_places=3, null=True, description="来源数量")
    raw_data = fields.JSONField(null=True, description="原始行数据")
    handling_status = fields.CharEnumField(
        enum_type=HandlingStatus,
        max_length=10,
        default=HandlingStatus.open,
        db_index=True,
        description="人工处理状态",
    )
    handling_note = fields.CharField(max_length=500, null=True, description="人工处理说明")
    handled_at = fields.DatetimeField(null=True, description="处理时间")
    handled_by = fields.CharField(max_length=64, null=True, description="处理人")
    duplicate_of_row_id: int | None
    duplicate_of_row = fields.ForeignKeyField(
        "app_system.MonthlyImportRow",
        null=True,
        related_name="duplicates",
        on_delete=fields.SET_NULL,
        description="重复来源行",
    )
    note = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_monthly_import_row"
        table_description = "导入原始明细"
        unique_together = (("batch", "row_number"),)


class WorkTicket(BaseModel, AuditMixin):
    """工票台账"""

    id = fields.IntField(primary_key=True)
    work_month_id: int
    work_month = fields.ForeignKeyField(
        "app_system.WorkMonth",
        related_name="tickets",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="月度任务",
    )
    order_id: int | None
    order = fields.ForeignKeyField(
        "app_system.Order",
        null=True,
        related_name="work_tickets",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="关联订单",
    )
    order_no_snapshot = fields.CharField(max_length=100, null=True, description="订单号快照")
    part_no_snapshot = fields.CharField(max_length=200, null=True, db_index=True, description="项目号快照")
    name_snapshot = fields.CharField(max_length=200, null=True, description="名称快照")
    ticket_code = fields.CharField(max_length=100, null=True, db_index=True, description="工票码")
    ticket_code_key = fields.CharField(max_length=100, null=True, db_index=True, description="工票码比较键")
    code_source = fields.CharEnumField(
        enum_type=TicketCodeSource,
        max_length=10,
        default=TicketCodeSource.none,
        description="工票码来源",
    )
    code_rule_version = fields.CharField(max_length=20, null=True, description="工票码规则版本")
    code_confidence = fields.DecimalField(max_digits=5, decimal_places=4, null=True, description="OCR 置信度")
    source_import_row_id: int | None
    source_import_row = fields.ForeignKeyField(
        "app_system.MonthlyImportRow",
        null=True,
        related_name="tickets",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="来源导入行",
    )
    status = fields.CharEnumField(
        enum_type=TicketStatus,
        max_length=10,
        default=TicketStatus.active,
        db_index=True,
        description="工票状态",
    )
    reconcile_status = fields.CharEnumField(
        enum_type=ReconcileStatus,
        max_length=10,
        default=ReconcileStatus.pending,
        db_index=True,
        description="核对状态",
    )
    reconcile_note = fields.CharField(max_length=500, null=True, description="核对说明")
    void_reason = fields.CharField(max_length=500, null=True, description="作废原因")
    voided_at = fields.DatetimeField(null=True, description="作废时间")
    voided_by = fields.CharField(max_length=64, null=True, description="作废人")
    remark = fields.CharField(max_length=500, null=True, description="备注")
    revision = fields.IntField(default=1, description="修订版本")

    class Meta:
        table = "biz_work_ticket_management_work_ticket"
        table_description = "工票台账"
        unique_together = (("work_month", "ticket_code_key"),)


class WorkTicketAssignment(BaseModel, AuditMixin):
    """工票人员分配"""

    id = fields.IntField(primary_key=True)
    ticket_id: int
    ticket = fields.ForeignKeyField(
        "app_system.WorkTicket",
        related_name="assignments",
        on_delete=fields.RESTRICT,
        description="工票",
    )
    worker_id: int
    worker = fields.ForeignKeyField(
        "app_system.Worker",
        related_name="ticket_assignments",
        on_delete=fields.RESTRICT,
        db_index=True,
        description="生产人员",
    )
    source = fields.CharEnumField(
        enum_type=AssignmentSource,
        max_length=10,
        default=AssignmentSource.manual,
        description="分配来源",
    )
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_work_ticket_assignment"
        table_description = "工票人员分配"
        unique_together = (("ticket", "worker"),)


class WorkTimeEntry(BaseModel, AuditMixin):
    """工时明细"""

    id = fields.IntField(primary_key=True)
    assignment_id: int
    assignment = fields.ForeignKeyField(
        "app_system.WorkTicketAssignment",
        related_name="time_entries",
        on_delete=fields.RESTRICT,
        description="工票人员分配",
    )
    work_date = fields.DateField(db_index=True, description="实际工作日期")
    accounting_month = fields.CharField(max_length=7, null=True, db_index=True, description="跨月归属月份 YYYY-MM")
    hours = fields.DecimalField(max_digits=5, decimal_places=2, description="工时小时")
    remark = fields.CharField(max_length=500, null=True, description="备注")

    class Meta:
        table = "biz_work_ticket_management_work_time_entry"
        table_description = "工时明细"
        unique_together = (("assignment", "work_date"),)


class WorkMonthStatusLog(BaseModel, AuditMixin):
    """月度状态日志"""

    id = fields.IntField(primary_key=True)
    work_month_id: int
    work_month = fields.ForeignKeyField(
        "app_system.WorkMonth",
        related_name="status_logs",
        on_delete=fields.CASCADE,
        db_index=True,
        description="月度任务",
    )
    from_status = fields.CharEnumField(
        enum_type=WorkMonthStatus,
        max_length=20,
        null=True,
        description="原状态",
    )
    to_status = fields.CharEnumField(
        enum_type=WorkMonthStatus,
        max_length=20,
        description="新状态",
    )
    action = fields.CharEnumField(
        enum_type=WorkMonthAction,
        max_length=10,
        description="动作",
    )
    reason = fields.CharField(max_length=500, null=True, description="原因")
    summary = fields.JSONField(null=True, description="状态变更统计快照")

    class Meta:
        table = "biz_work_ticket_management_work_month_status_log"
        table_description = "月度状态日志"
