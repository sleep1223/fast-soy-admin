# pyright: reportIncompatibleVariableOverride=false
"""
labor_management — 请求/响应 Schema。
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.utils import PageQueryBase, SchemaBase, SqidId


class LaborProjectBase(SchemaBase):
    part_no: Annotated[str, Field(max_length=200)] | None = Field(None, title="项目号")
    skip_painting: bool | None = Field(None, title="无需刷漆")


class LaborProjectCreate(LaborProjectBase):
    part_no: Annotated[str, Field(max_length=200)] = Field(title="项目号")
    skip_painting: bool = Field(False, title="无需刷漆")


class LaborProjectUpdate(LaborProjectBase):
    imported_at: datetime | None = Field(None, title="导入时间")


class LaborProjectSearch(LaborProjectBase, PageQueryBase):
    imported_at_start: datetime | None = Field(None, title="导入时间开始")
    imported_at_end: datetime | None = Field(None, title="导入时间结束")


# ============================================================
# 劳务人员
# ============================================================


class LaborWorkerBase(SchemaBase):
    employee_no: Annotated[str, Field(max_length=100)] | None = Field(None, title="工号")
    trade: Annotated[str, Field(max_length=100)] | None = Field(None, title="工种")
    name: Annotated[str, Field(max_length=100)] | None = Field(None, title="姓名")
    remark: str | None = Field(None, title="备注")


class LaborWorkerCreate(LaborWorkerBase):
    employee_no: Annotated[str, Field(max_length=100)] = Field(title="工号")
    trade: Annotated[str, Field(max_length=100)] = Field(title="工种")
    name: Annotated[str, Field(max_length=100)] = Field(title="姓名")


class LaborWorkerUpdate(LaborWorkerBase): ...


class LaborWorkerSearch(LaborWorkerBase, PageQueryBase):
    pass


# ============================================================
# 工票对应的工时
# ============================================================


class LaborWorkHourBase(SchemaBase):
    ticket_code: Annotated[str, Field(max_length=100)] | None = Field(None, title="工票码")
    work_hours: Decimal | None = Field(None, title="工时（小时）")
    order_no: Annotated[str, Field(max_length=100)] | None = Field(None, title="订单号")
    worker_id: SqidId | None = Field(None, title="劳务人员")
    allocation_month: date | None = Field(None, title="分配月份")

    @field_validator("allocation_month")
    @classmethod
    def normalize_allocation_month(cls, value: date | None) -> date | None:
        return value.replace(day=1) if value else None


class LaborWorkHourCreate(LaborWorkHourBase):
    ticket_code: Annotated[str, Field(max_length=100)] = Field(title="工票码")
    work_hours: Decimal = Field(title="工时（小时）")
    order_no: Annotated[str, Field(max_length=100)] = Field(title="订单号")


class LaborWorkHourUpdate(LaborWorkHourBase): ...


class LaborWorkHourSearch(LaborWorkHourBase, PageQueryBase):
    is_assigned: bool | None = Field(None, title="是否已分配")
    order_nos: list[Annotated[str, Field(min_length=1, max_length=100)]] | None = Field(None, max_length=100, title="订单号列表")
