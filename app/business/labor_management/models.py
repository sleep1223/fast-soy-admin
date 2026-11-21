# pyright: reportIncompatibleVariableOverride=false
"""劳务人员与工票工时模型。"""

from tortoise import fields

from app.utils import AuditMixin, BaseModel


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

    class Meta:
        table = "biz_labor_management_work_hour"
        table_description = "工票工时"
