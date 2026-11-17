# pyright: reportIncompatibleVariableOverride=false
"""
order_management — 业务模型定义。

在此文件中定义 Tortoise ORM 模型，完成后运行:

    just cli-crud order_management

即可一次生成后端 schemas / controllers / api 及前端 service / views / i18n 等文件。
"""

from tortoise import fields

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
#     # 仅当本模块在 config.py 声明了独立 DB_URL 时，才改用 "app_order_management.<Model>"。
#     # parent_id: int | None
#     # parent: fields.ForeignKeyNullableRelation["Example"] = fields.ForeignKeyField(
#     #     "app_system.Example", null=True, related_name="children", description="父节点",
#     # )
#
#     class Meta:
#         table = "biz_order_management_example"
#         table_description = "示例"


# pyright: reportIncompatibleVariableOverride=false
"""订单管理 — 业务模型定义。"""


class Order(BaseModel, AuditMixin):
    """订单资料"""

    id = fields.IntField(primary_key=True)

    order_no = fields.CharField(
        max_length=100,
        unique=True,
        description="订单号",
    )

    part_no = fields.CharField(
        max_length=200,
        db_index=True,
        description="项目号",
    )

    name = fields.CharField(
        max_length=200,
        description="名称",
    )

    net_weight = fields.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        description="净重",
    )

    gross_weight = fields.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        description="毛重",
    )

    unit = fields.CharField(
        max_length=50,
        null=True,
        description="单位",
    )

    quantity = fields.IntField(
        null=True,
        description="数量",
    )

    received_quantity = fields.IntField(
        null=True,
        description="入库数量",
    )

    total_weight = fields.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        description="合计重量",
    )

    order_due_date = fields.DateField(
        null=True,
        description="订单完工期",
    )

    completed_date = fields.DateField(
        null=True,
        description="实际完工期",
    )

    process_route = fields.CharField(
        max_length=500,
        null=True,
        description="工艺路线",
    )

    customer = fields.CharField(
        max_length=200,
        null=True,
        description="用户",
    )

    class Meta:
        table = "biz_order_management_order"
        table_description = "订单资料"
