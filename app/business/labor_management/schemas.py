# pyright: reportIncompatibleVariableOverride=false
"""
labor_management — 请求/响应 Schema。
"""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field, field_validator

from app.utils import PageQueryBase, SchemaBase, SqidId


class LaborProjectBase(SchemaBase):
    part_no: Annotated[str, Field(max_length=200)] | None = Field(None, title="项目号")


class LaborProjectCreate(LaborProjectBase):
    part_no: Annotated[str, Field(max_length=200)] = Field(title="项目号")


class LaborProjectUpdate(LaborProjectBase): ...


class LaborProjectSearch(LaborProjectBase, PageQueryBase):
    pass


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
    worker_id: SqidId = Field(title="劳务人员")


class LaborWorkHourUpdate(LaborWorkHourBase): ...


class LaborWorkHourSearch(LaborWorkHourBase, PageQueryBase):
    pass
