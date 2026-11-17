# pyright: reportIncompatibleVariableOverride=false
"""
weighbridge_settlement — 请求/响应 Schema。
"""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import ConfigDict, Field, field_validator

from app.utils import Int32, PageQueryBase, SchemaBase, SchemaValidationError, SqidId, make_optional

TicketImage = Annotated[str, Field(pattern=r"^/system-manage/uploads/content/[0-9a-f]{32}$")]

# ============================================================
# 工序招采价格
# ============================================================


class SettlementRateBase(SchemaBase):
    process_name: Annotated[str, Field(max_length=100)] | None = Field(None, title="工序名称")
    price: Decimal | None = Field(None, title="含税招采价格（元/kg）")
    enabled: bool | None = Field(None, title="是否启用")


class SettlementRateCreate(SettlementRateBase):
    model_config = ConfigDict(str_strip_whitespace=True)
    process_name: Annotated[str, Field(min_length=1, max_length=100)] = Field(title="工序名称")
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=4, title="含税招采价格（元/kg）")

    # make_optional preserves validators, but not Field metadata; validate both create and update.
    @field_validator("price")
    @classmethod
    def valid_price(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and (not value.is_finite() or value <= 0 or value >= Decimal("1e6") or value != value.quantize(Decimal(".0001"))):
            raise SchemaValidationError(code="4601", msg="招采价格必须大于零，最多四位小数且不超过存储范围")
        return value

    @field_validator("process_name")
    @classmethod
    def valid_process_name(cls, value: str | None) -> str | None:
        if value is not None and (not value or len(value) > 100):
            raise SchemaValidationError(code="4601", msg="工序名称不能为空且不能超过100字符")
        return value


SettlementRateUpdate = make_optional(SettlementRateCreate, "SettlementRateUpdate")


class SettlementRateSearch(SettlementRateBase, PageQueryBase):
    pass


# ============================================================
# 磅单信息
# ============================================================


class WeighingTicketBase(SchemaBase):
    ticket_no: Annotated[str, Field(max_length=100)] | None = Field(None, title="磅单编号")
    weighing_date: date | None = Field(None, title="过磅日期")
    weight: Decimal | None = Field(None, title="实际过磅重量/kg")
    process: Annotated[str, Field(max_length=100)] | None = Field(None, title="工序名称快照")
    price: Decimal | None = Field(None, title="含税价格快照（元/kg）")
    total_amount: Decimal | None = Field(None, title="含税总金额/元")
    is_settled: bool | None = Field(None, title="是否已结算")
    revision: Int32 | None = Field(None, title="修订版本")
    rate_id: SqidId | None = Field(None, title="工序招采价格")


class WeighingLineInput(SchemaBase):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: SqidId | None = None
    order_id: SqidId | None = None
    order_no: str | None = Field(None, max_length=100)
    part_no: str = Field("", max_length=200)
    name: str = Field("", max_length=200)
    net_weight: Decimal | None = Field(None, gt=0, max_digits=16, decimal_places=6)
    gross_weight: Decimal | None = Field(None, gt=0, max_digits=16, decimal_places=6)
    quantity: int = Field(gt=0, le=2147483647, strict=True)


class WeighingTicketCreate(SchemaBase):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    ticket_no: str = Field(min_length=1, max_length=100)
    weighing_date: date
    weight: Decimal = Field(gt=0, max_digits=16, decimal_places=3)
    rate_id: SqidId
    images: list[TicketImage] | None = Field(None, max_length=5, title="磅单图片")
    lines: list[WeighingLineInput] = Field(min_length=1, max_length=500)


class WeighingTicketUpdate(WeighingTicketCreate):
    # Full aggregate submission; omitting rate_id preserves the historical price snapshot.
    rate_id: SqidId | None = None
    revision: int = Field(ge=1, le=2147483646, strict=True)


class RevisionInput(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1, le=2147483646, strict=True)


class OrderLookup(SchemaBase):
    part_no: str = Field(min_length=1, max_length=200)
    limit: int = Field(20, ge=1, le=50)


class PreviewInput(SchemaBase):
    weight: Decimal = Field(gt=0, max_digits=16, decimal_places=3)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=4)
    lines: list[WeighingLineInput] = Field(min_length=1, max_length=500)


class WeighingTicketSearch(WeighingTicketBase, PageQueryBase):
    weighing_date_start: date | None = Field(None, title="过磅日期开始")
    weighing_date_end: date | None = Field(None, title="过磅日期结束")


MAX_EXPORT_ROWS = 10000


class WeighingTicketExport(WeighingTicketSearch):
    ids: list[SqidId] | None = Field(None, min_length=1, max_length=MAX_EXPORT_ROWS, title="所选记录 ID")


class WeighingLineOut(SchemaBase):
    id: SqidId
    order_id: SqidId | None
    order_no: str | None
    part_no: str
    name: str
    net_weight: Decimal | None
    gross_weight: Decimal | None
    quantity: int
    position: int
    theoretical_weight: Decimal
    allocated_weight: Decimal
    amount: Decimal
    tax_unit_price: Decimal


class WeighingTicketOut(SchemaBase):
    id: SqidId
    ticket_no: str = Field(title="磅单编号")
    weighing_date: date = Field(title="过磅日期")
    images: list[str] | None = Field(None, title="磅单图片")
    weight: Decimal = Field(title="实际过磅重量/kg")
    rate_id: SqidId = Field(title="工序招采价格")
    process: str = Field(title="工序名称快照")
    price: Decimal = Field(title="含税价格快照（元/kg）")
    total_amount: Decimal = Field(title="含税总金额/元")
    is_settled: bool = Field(title="是否已结算")
    revision: int = Field(title="修订版本")
    lines: list[WeighingLineOut]
