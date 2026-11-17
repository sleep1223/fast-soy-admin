# pyright: reportIncompatibleVariableOverride=false
"""
weighbridge_settlement — 业务模型定义。

在此文件中定义 Tortoise ORM 模型，完成后运行:

    just cli-crud weighbridge_settlement

即可一次生成后端 schemas / controllers / api 及前端 service / views / i18n 等文件。
"""

from __future__ import annotations

from tortoise import fields
from tortoise.models import Model

from app.utils import AuditMixin, BaseModel

# ---- 在下方定义你的模型 ----
#
# class Example(BaseModel, AuditMixin):
#     """示例"""
#
#     id = fields.IntField(primary_key=True)
#     name = fields.CharField(max_length=100, description="名称")
#     status = fields.CharEnumField(enum_type=StatusType, default=StatusType.enable, description="状态")
#
#     # 外键规范：必须在 FK 字段上方声明 <name>_id: int（非空）或 int | None（可空）
#     # 使用时创建/更新/比较一律用 parent_id，访问关系对象字段前先 prefetch_related("parent")。
#     # 关联模型字符串使用 "app_system.<Model>"（默认情况下业务模块模型都注册到 app_system）；
#     # 仅当本模块在 config.py 声明了独立 DB_URL 时，才改用 "app_weighbridge_settlement.<Model>"。
#     # parent_id: int | None
#     # parent: fields.ForeignKeyNullableRelation["Example"] = fields.ForeignKeyField(
#     #     "app_system.Example", null=True, related_name="children", description="父节点",
#     # )
#
#     class Meta:
#         table = "biz_weighbridge_settlement_example"
#         table_description = "示例"


class SettlementRate(BaseModel, AuditMixin):
    """工序招采价格"""

    id = fields.IntField(primary_key=True)

    process_name = fields.CharField(
        max_length=100,
        unique=True,
        description="工序名称",
    )

    price = fields.DecimalField(
        max_digits=10,
        decimal_places=4,
        description="含税招采价格（元/kg）",
    )

    enabled = fields.BooleanField(
        default=True,
        description="是否启用",
    )

    class Meta:
        table = "biz_settlement_rate"
        table_description = "工序招采价格"


class WeighingTicket(BaseModel, AuditMixin):
    """磅单信息"""

    id = fields.IntField(primary_key=True)

    ticket_no = fields.CharField(
        max_length=100,
        unique=True,
        description="磅单编号",
    )

    weighing_date = fields.DateField(
        db_index=True,
        description="过磅日期",
    )

    images = fields.JSONField(
        null=True,
        description="磅单图片 [images]",
    )

    weight = fields.DecimalField(
        max_digits=16,
        decimal_places=3,
        description="实际过磅重量/kg",
    )

    # 自定义工序价格关联
    rate_id: int
    rate: fields.ForeignKeyRelation[SettlementRate] = fields.ForeignKeyField(
        "app_system.SettlementRate",
        related_name="tickets",
        on_delete=fields.RESTRICT,
        description="工序招采价格",
    )

    process = fields.CharField(
        max_length=100,
        description="工序名称快照",
    )

    price = fields.DecimalField(
        max_digits=10,
        decimal_places=4,
        description="含税价格快照（元/kg）",
    )

    total_amount = fields.DecimalField(
        max_digits=20,
        decimal_places=2,
        description="含税总金额/元",
    )

    is_settled = fields.BooleanField(
        default=False,
        description="是否已结算",
    )

    revision = fields.IntField(
        default=1,
        description="修订版本",
    )

    class Meta:
        table = "biz_settlement_ticket"
        table_description = "磅单信息"


class WeighingLine(BaseModel, AuditMixin):
    """磅单结算明细"""

    id = fields.IntField(primary_key=True)

    # 关联磅单
    ticket_id: int
    ticket: fields.ForeignKeyRelation[WeighingTicket] = fields.ForeignKeyField(
        "app_system.WeighingTicket",
        related_name="lines",
        on_delete=fields.CASCADE,
        description="所属磅单",
    )

    # 关联订单资料
    order_id: int | None

    order: fields.ForeignKeyNullableRelation[Model] = fields.ForeignKeyField(
        "app_system.Order",
        null=True,
        related_name="weighing_lines",
        on_delete=fields.RESTRICT,
        description="关联订单",
    )

    position = fields.IntField(
        description="明细顺序",
    )

    # 订单资料快照
    order_no = fields.CharField(
        max_length=100,
        null=True,
        description="订单号快照",
    )

    part_no = fields.CharField(
        max_length=200,
        description="项目号快照",
    )

    name = fields.CharField(
        max_length=200,
        description="名称快照",
    )

    net_weight = fields.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        description="净重快照",
    )

    gross_weight = fields.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        description="毛重快照",
    )

    # 本次实际过磅数量
    quantity = fields.IntField(
        description="实际过磅数量",
    )

    theoretical_weight = fields.DecimalField(
        max_digits=24,
        decimal_places=6,
        description="机内合重/kg",
    )

    allocated_weight = fields.DecimalField(
        max_digits=16,
        decimal_places=3,
        description="分摊过磅重量/kg",
    )

    amount = fields.DecimalField(
        max_digits=20,
        decimal_places=2,
        description="含税结算金额/元",
    )

    tax_unit_price = fields.DecimalField(
        max_digits=20,
        decimal_places=6,
        description="含税单价（元/件）",
    )

    class Meta:
        table = "biz_settlement_line"
        table_description = "磅单结算明细"

        unique_together = (
            ("ticket", "position"),
            ("ticket", "order"),
        )
