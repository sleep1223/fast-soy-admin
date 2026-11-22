# pyright: reportIncompatibleVariableOverride=false
"""
order_management — 请求/响应 Schema。
"""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from app.utils import Int32, PageQueryBase, SchemaBase

# ============================================================
# 订单资料
# ============================================================


class OrderBase(SchemaBase):
    order_no: Annotated[str, Field(max_length=100)] | None = Field(None, title="订单号")
    part_no: Annotated[str, Field(max_length=200)] | None = Field(None, title="项目号")
    name: Annotated[str, Field(max_length=200)] | None = Field(None, title="名称")
    net_weight: Decimal | None = Field(None, title="净重")
    gross_weight: Decimal | None = Field(None, ge=0, max_digits=16, decimal_places=6, title="毛重")
    unit: Annotated[str, Field(max_length=50)] | None = Field(None, title="单位")
    quantity: Int32 | None = Field(None, title="数量")
    received_quantity: Int32 | None = Field(None, title="入库数量")
    total_weight: Decimal | None = Field(None, title="合计重量")
    order_due_date: date | None = Field(None, title="订单完工期")
    completed_date: date | None = Field(None, title="实际完工期")
    process_route: Annotated[str, Field(max_length=500)] | None = Field(None, title="工艺路线")
    customer: Annotated[str, Field(max_length=200)] | None = Field(None, title="用户")


class OrderCreate(OrderBase):
    order_no: Annotated[str, Field(max_length=100)] = Field(title="订单号")
    part_no: Annotated[str, Field(max_length=200)] = Field(title="项目号")
    name: Annotated[str, Field(max_length=200)] = Field(title="名称")
    net_weight: Decimal | None = Field(None, title="净重")


class OrderUpdate(OrderBase): ...


class OrderSearch(OrderBase, PageQueryBase):
    part_nos: list[Annotated[str, Field(min_length=1, max_length=200)]] | None = Field(None, max_length=100, title="项目号列表")
    order_due_date_start: date | None = Field(None, title="订单完工期开始")
    order_due_date_end: date | None = Field(None, title="订单完工期结束")
    completed_date_start: date | None = Field(None, title="实际完工期开始")
    completed_date_end: date | None = Field(None, title="实际完工期结束")
