"""项目、订单、工票和分配工作台的请求及响应。"""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BeforeValidator, Field, model_validator

from app.utils import PageQueryBase, SchemaBase, SqidId

Hours = Annotated[Decimal, Field(ge=0, max_digits=7, decimal_places=2)]


def excel_part_no(value: object) -> str:
    # Excel 数字单元格不保留前导零，带前导零的项目号应使用文本单元格。
    if isinstance(value, str):
        return value.strip()
    if type(value) is int:
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    raise ValueError("项目号应为文本或整数")


class WorkProjectImportRow(SchemaBase):
    part_no: Annotated[str, Field(min_length=1, max_length=200), BeforeValidator(excel_part_no)]


class WorkProjectImportOut(SchemaBase):
    imported_count: int
    created_count: int
    matched_order_count: int
    unmatched_project_count: int


class WorkProjectSearch(PageQueryBase):
    part_no: Annotated[str, Field(max_length=200)] | None = None


class WorkProjectOut(SchemaBase):
    id: SqidId
    part_no: str
    order_count: int


class WorkProjectOrderOut(SchemaBase):
    id: SqidId
    order_no: str
    name: str
    ticket_count: int


class WorkAssetTicketCreate(SchemaBase):
    ticket_code: Annotated[str, Field(min_length=1, max_length=100)]
    code_source: Literal["manual", "ocr"] = "manual"
    total_hours: Hours | None = None


class WorkAssetAllocationCreate(SchemaBase):
    worker_id: SqidId
    assigned_on: date = Field(default_factory=date.today)
    hours: Hours | None = None


class WorkAssetAllocationUpdate(SchemaBase):
    worker_id: SqidId
    assigned_on: date
    hours: Hours | None = None


class WorkAssetAllocationOut(SchemaBase):
    id: SqidId
    worker_id: SqidId
    worker_name: str
    assigned_on: date
    hours: Decimal | None


class WorkAssetTicketOut(SchemaBase):
    id: SqidId
    ticket_code: str
    code_source: str
    total_hours: Decimal | None
    assigned_hours: Decimal
    allocations: list[WorkAssetAllocationOut]


class WorkAssetReportSearch(SchemaBase):
    start_date: date
    end_date: date
    production_unit_id: SqidId | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("结束日期不能早于开始日期")
        return self


class WorkAssetReportRow(SchemaBase):
    worker_id: SqidId
    worker_name: str
    production_unit_name: str | None
    allocation_count: int
    hours: Decimal
