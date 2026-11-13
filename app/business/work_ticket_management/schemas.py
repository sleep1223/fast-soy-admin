# pyright: reportIncompatibleVariableOverride=false
"""
work_ticket_management — 请求/响应 Schema。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.business.work_ticket_management.models import (
    AssignmentSource,
    HandlingStatus,
    ImportBatchStatus,
    ImportSourceType,
    MatchSource,
    MatchStatus,
    ReconcileStatus,
    TicketCodeSource,
    TicketStatus,
    WorkMonthAction,
    WorkMonthStatus,
)
from app.utils import Int32, PageQueryBase, SchemaBase, SqidId

# ============================================================
# 生产单位
# ============================================================


class ProductionUnitBase(SchemaBase):
    code: Annotated[str, Field(max_length=50)] | None = Field(None, title="单位编码")
    name: Annotated[str, Field(max_length=100)] | None = Field(None, title="单位名称")
    enabled: bool | None = Field(None, title="是否启用")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")


class ProductionUnitCreate(ProductionUnitBase):
    code: Annotated[str, Field(max_length=50)] = Field(title="单位编码")
    name: Annotated[str, Field(max_length=100)] = Field(title="单位名称")


class ProductionUnitUpdate(ProductionUnitBase): ...


class ProductionUnitSearch(ProductionUnitBase, PageQueryBase):
    pass


# ============================================================
# 生产人员
# ============================================================


class WorkerBase(SchemaBase):
    worker_no: Annotated[str, Field(max_length=50)] | None = Field(None, title="人员编号")
    name: Annotated[str, Field(max_length=100)] | None = Field(None, title="姓名")
    enabled: bool | None = Field(None, title="是否在用")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    production_unit_id: SqidId | None = Field(None, title="默认所属生产单位")


class WorkerCreate(WorkerBase):
    name: Annotated[str, Field(max_length=100)] = Field(title="姓名")


class WorkerUpdate(WorkerBase): ...


class WorkerSearch(WorkerBase, PageQueryBase):
    pass


# ============================================================
# 订单与生产单位关系
# ============================================================


class OrderUnitMappingBase(SchemaBase):
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    order_id: SqidId | None = Field(None, title="订单")
    production_unit_id: SqidId | None = Field(None, title="生产单位")


class OrderUnitMappingCreate(OrderUnitMappingBase):
    order_id: SqidId = Field(title="订单")
    production_unit_id: SqidId = Field(title="生产单位")


class OrderUnitMappingUpdate(OrderUnitMappingBase): ...


class OrderUnitMappingSearch(OrderUnitMappingBase, PageQueryBase):
    pass


# ============================================================
# 月度任务
# ============================================================


class WorkMonthBase(SchemaBase):
    year_month: Annotated[str, Field(max_length=7)] | None = Field(None, title="归属月份 YYYY-MM")
    status: WorkMonthStatus | None = Field(None, title="状态")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    revision: Int32 | None = Field(None, title="修订版本")
    closed_at: datetime | None = Field(None, title="关闭时间")
    closed_by: Annotated[str, Field(max_length=64)] | None = Field(None, title="关闭人")
    reopened_at: datetime | None = Field(None, title="最近重开时间")
    reopen_count: Int32 | None = Field(None, title="重开次数")
    production_unit_id: SqidId | None = Field(None, title="生产单位")


class WorkMonthCreate(WorkMonthBase):
    year_month: Annotated[str, Field(max_length=7)] = Field(title="归属月份 YYYY-MM")
    production_unit_id: SqidId = Field(title="生产单位")


class WorkMonthUpdate(WorkMonthBase): ...


class WorkMonthSearch(WorkMonthBase, PageQueryBase):
    closed_at_start: datetime | None = Field(None, title="关闭时间开始")
    closed_at_end: datetime | None = Field(None, title="关闭时间结束")
    reopened_at_start: datetime | None = Field(None, title="最近重开时间开始")
    reopened_at_end: datetime | None = Field(None, title="最近重开时间结束")


# ============================================================
# 月度导入批次
# ============================================================


class MonthlyImportBatchBase(SchemaBase):
    source_type: ImportSourceType | None = Field(None, title="来源类型")
    status: ImportBatchStatus | None = Field(None, title="批次状态")
    source_name: Annotated[str, Field(max_length=255)] | None = Field(None, title="来源文件名或说明")
    content_hash: Annotated[str, Field(max_length=64)] | None = Field(None, title="文件内容 SHA-256")
    row_count: Int32 | None = Field(None, title="来源数据行数")
    void_reason: Annotated[str, Field(max_length=500)] | None = Field(None, title="作废原因")
    voided_at: datetime | None = Field(None, title="作废时间")
    voided_by: Annotated[str, Field(max_length=64)] | None = Field(None, title="作废人")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    work_month_id: SqidId | None = Field(None, title="月度任务")


class MonthlyImportBatchCreate(MonthlyImportBatchBase):
    source_type: ImportSourceType = Field(title="来源类型")
    work_month_id: SqidId = Field(title="月度任务")


class MonthlyImportBatchUpdate(MonthlyImportBatchBase): ...


class MonthlyImportBatchSearch(MonthlyImportBatchBase, PageQueryBase):
    voided_at_start: datetime | None = Field(None, title="作废时间开始")
    voided_at_end: datetime | None = Field(None, title="作废时间结束")


# ============================================================
# 导入原始明细
# ============================================================


class MonthlyImportRowBase(SchemaBase):
    row_number: Int32 | None = Field(None, title="源文件行号")
    raw_part_no: Annotated[str, Field(max_length=200)] | None = Field(None, title="原始项目号")
    normalized_part_no: Annotated[str, Field(max_length=200)] | None = Field(None, title="规范化项目号")
    match_status: MatchStatus | None = Field(None, title="订单匹配状态")
    match_source: MatchSource | None = Field(None, title="匹配方式")
    source_quantity: Decimal | None = Field(None, title="来源数量")
    raw_data: dict | None = Field(None, title="原始行数据")
    handling_status: HandlingStatus | None = Field(None, title="人工处理状态")
    handling_note: Annotated[str, Field(max_length=500)] | None = Field(None, title="人工处理说明")
    handled_at: datetime | None = Field(None, title="处理时间")
    handled_by: Annotated[str, Field(max_length=64)] | None = Field(None, title="处理人")
    note: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    batch_id: SqidId | None = Field(None, title="导入批次")
    order_id: SqidId | None = Field(None, title="匹配订单")
    duplicate_of_row_id: SqidId | None = Field(None, title="重复来源行")


class MonthlyImportRowCreate(MonthlyImportRowBase):
    row_number: Int32 = Field(title="源文件行号")
    raw_part_no: Annotated[str, Field(max_length=200)] = Field(title="原始项目号")
    normalized_part_no: Annotated[str, Field(max_length=200)] = Field(title="规范化项目号")
    batch_id: SqidId = Field(title="导入批次")


class MonthlyImportRowUpdate(MonthlyImportRowBase): ...


class MonthlyImportRowSearch(MonthlyImportRowBase, PageQueryBase):
    handled_at_start: datetime | None = Field(None, title="处理时间开始")
    handled_at_end: datetime | None = Field(None, title="处理时间结束")


# ============================================================
# 工票台账
# ============================================================


class WorkTicketBase(SchemaBase):
    order_no_snapshot: Annotated[str, Field(max_length=100)] | None = Field(None, title="订单号快照")
    part_no_snapshot: Annotated[str, Field(max_length=200)] | None = Field(None, title="项目号快照")
    name_snapshot: Annotated[str, Field(max_length=200)] | None = Field(None, title="名称快照")
    ticket_code: Annotated[str, Field(max_length=100)] | None = Field(None, title="工票码")
    ticket_code_key: Annotated[str, Field(max_length=100)] | None = Field(None, title="工票码比较键")
    code_source: TicketCodeSource | None = Field(None, title="工票码来源")
    code_rule_version: Annotated[str, Field(max_length=20)] | None = Field(None, title="工票码规则版本")
    code_confidence: Decimal | None = Field(None, title="OCR 置信度")
    status: TicketStatus | None = Field(None, title="工票状态")
    reconcile_status: ReconcileStatus | None = Field(None, title="核对状态")
    reconcile_note: Annotated[str, Field(max_length=500)] | None = Field(None, title="核对说明")
    void_reason: Annotated[str, Field(max_length=500)] | None = Field(None, title="作废原因")
    voided_at: datetime | None = Field(None, title="作废时间")
    voided_by: Annotated[str, Field(max_length=64)] | None = Field(None, title="作废人")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    revision: Int32 | None = Field(None, title="修订版本")
    work_month_id: SqidId | None = Field(None, title="月度任务")
    order_id: SqidId | None = Field(None, title="关联订单")
    source_import_row_id: SqidId | None = Field(None, title="来源导入行")


class WorkTicketCreate(WorkTicketBase):
    work_month_id: SqidId = Field(title="月度任务")


class WorkTicketUpdate(WorkTicketBase): ...


class WorkTicketSearch(WorkTicketBase, PageQueryBase):
    voided_at_start: datetime | None = Field(None, title="作废时间开始")
    voided_at_end: datetime | None = Field(None, title="作废时间结束")


# ============================================================
# 工票人员分配
# ============================================================


class WorkTicketAssignmentBase(SchemaBase):
    source: AssignmentSource | None = Field(None, title="分配来源")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    ticket_id: SqidId | None = Field(None, title="工票")
    worker_id: SqidId | None = Field(None, title="生产人员")


class WorkTicketAssignmentCreate(WorkTicketAssignmentBase):
    ticket_id: SqidId = Field(title="工票")
    worker_id: SqidId = Field(title="生产人员")


class WorkTicketAssignmentUpdate(WorkTicketAssignmentBase): ...


class WorkTicketAssignmentSearch(WorkTicketAssignmentBase, PageQueryBase):
    pass


# ============================================================
# 工时明细
# ============================================================


class WorkTimeEntryBase(SchemaBase):
    work_date: date | None = Field(None, title="实际工作日期")
    accounting_month: Annotated[str, Field(max_length=7)] | None = Field(None, title="跨月归属月份 YYYY-MM")
    hours: Decimal | None = Field(None, title="工时小时")
    remark: Annotated[str, Field(max_length=500)] | None = Field(None, title="备注")
    assignment_id: SqidId | None = Field(None, title="工票人员分配")


class WorkTimeEntryCreate(WorkTimeEntryBase):
    work_date: date = Field(title="实际工作日期")
    hours: Decimal = Field(title="工时小时")
    assignment_id: SqidId = Field(title="工票人员分配")


class WorkTimeEntryUpdate(WorkTimeEntryBase): ...


class WorkTimeEntrySearch(WorkTimeEntryBase, PageQueryBase):
    work_date_start: date | None = Field(None, title="实际工作日期开始")
    work_date_end: date | None = Field(None, title="实际工作日期结束")


# ============================================================
# 月度状态日志
# ============================================================


class WorkMonthStatusLogBase(SchemaBase):
    from_status: WorkMonthStatus | None = Field(None, title="原状态")
    to_status: WorkMonthStatus | None = Field(None, title="新状态")
    action: WorkMonthAction | None = Field(None, title="动作")
    reason: Annotated[str, Field(max_length=500)] | None = Field(None, title="原因")
    summary: dict | None = Field(None, title="状态变更统计快照")
    work_month_id: SqidId | None = Field(None, title="月度任务")


class WorkMonthStatusLogCreate(WorkMonthStatusLogBase):
    to_status: WorkMonthStatus = Field(title="新状态")
    action: WorkMonthAction = Field(title="动作")
    work_month_id: SqidId = Field(title="月度任务")


class WorkMonthStatusLogUpdate(WorkMonthStatusLogBase): ...


class WorkMonthStatusLogSearch(WorkMonthStatusLogBase, PageQueryBase):
    pass
