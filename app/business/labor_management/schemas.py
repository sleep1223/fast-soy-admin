# pyright: reportIncompatibleVariableOverride=false
"""
labor_management — 请求/响应 Schema。
"""

from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.utils import PageQueryBase, SchemaBase

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


class LaborWorkHourCreate(LaborWorkHourBase):
    ticket_code: Annotated[str, Field(max_length=100)] = Field(title="工票码")
    work_hours: Decimal = Field(title="工时（小时）")
    order_no: Annotated[str, Field(max_length=100)] = Field(title="订单号")


class LaborWorkHourUpdate(LaborWorkHourBase): ...


class LaborWorkHourSearch(LaborWorkHourBase, PageQueryBase):
    pass
