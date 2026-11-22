# pyright: reportIncompatibleVariableOverride=false
"""劳务项目、人员与工票工时模型。"""

from tortoise import fields

from app.utils import AuditMixin, BaseModel


class LaborProject(BaseModel, AuditMixin):
    """劳务项目。"""

    id = fields.IntField(primary_key=True)
    # 与订单资料的 part_no 按值匹配，一个项目可对应多个订单。
    part_no = fields.CharField(max_length=200, unique=True, description="项目号")
    skip_painting = fields.BooleanField(default=False, db_default=False, description="无需刷漆")
    imported_at = fields.DatetimeField(null=True, description="首次导入时间")

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


class LaborWorkHour(BaseModel, AuditMixin):
    """工票对应的工时。"""

    id = fields.IntField(primary_key=True)
    ticket_code = fields.CharField(max_length=100, unique=True, description="工票码")
    work_hours = fields.DecimalField(max_digits=12, decimal_places=2, description="工时（小时）")
    order_no = fields.CharField(max_length=100, db_index=True, description="订单号")
    allocation_month = fields.DateField(null=True, db_index=True, description="分配月份")
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
