# pyright: reportIncompatibleVariableOverride=false
"""劳务项目、人员与工票工时模型。"""

from tortoise import fields

from app.utils import AuditMixin, BaseModel


class LaborProject(BaseModel, AuditMixin):
    """劳务项目。"""

    id = fields.IntField(primary_key=True)
    part_no = fields.CharField(max_length=200, unique=True, description="项目号")

    class Meta:
        table = "biz_labor_management_project"
        table_description = "劳务项目"


class LaborWorker(BaseModel, AuditMixin):
    """劳务人员。"""

    id = fields.IntField(primary_key=True)
    employee_no = fields.CharField(max_length=100, description="工号")
    trade = fields.CharField(max_length=100, description="工种")
    name = fields.CharField(max_length=100, description="姓名")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "biz_labor_management_worker"
        table_description = "劳务人员"


class LaborReceipt(BaseModel, AuditMixin):
    """月度接收工件明细。"""

    id = fields.IntField(primary_key=True)
    receipt_month = fields.DateField(db_index=True, description="接收月份")
    part_no = fields.CharField(max_length=200, db_index=True, description="项目号")

    class Meta:
        table = "biz_labor_management_receipt"
        table_description = "月度接收工件明细"
        unique_together = (("receipt_month", "part_no"),)


class LaborWorkHour(BaseModel, AuditMixin):
    """工票对应的工时。"""

    id = fields.IntField(primary_key=True)
    ticket_code = fields.CharField(max_length=100, unique=True, description="工票码")
    work_hours = fields.DecimalField(max_digits=12, decimal_places=2, description="工时（小时）")
    order_no = fields.CharField(max_length=100, db_index=True, description="订单号")
    allocation_month = fields.DateField(null=True, db_index=True, description="分配月份")
    receipt_id: int | None
    receipt: fields.ForeignKeyNullableRelation["LaborReceipt"] = fields.ForeignKeyField(
        "app_system.LaborReceipt",
        null=True,
        related_name="work_hours",
        on_delete=fields.RESTRICT,
        description="接收工件明细",
    )
    worker_id: int | None
    worker: fields.ForeignKeyNullableRelation["LaborWorker"] = fields.ForeignKeyField(
        "app_system.LaborWorker",
        null=True,
        related_name="work_hours",
        on_delete=fields.RESTRICT,
        description="劳务人员",
    )

    class Meta:
        table = "biz_labor_management_work_hour"
        table_description = "工票工时"
