from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0011_auto_20261121_0826')]

    initial = False

    operations = [
        ops.CreateModel(
            name='LaborWorkHour',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('ticket_code', fields.CharField(unique=True, description='工票码', max_length=100)),
                ('work_hours', fields.DecimalField(description='工时（小时）', max_digits=12, decimal_places=2)),
                ('order_no', fields.CharField(db_index=True, description='订单号', max_length=100)),
            ],
            options={'table': 'biz_labor_management_work_hour', 'app': 'app_system', 'pk_attr': 'id', 'table_description': '工票工时'},
            bases=['BaseModel', 'AuditMixin'],
        ),
        ops.CreateModel(
            name='LaborWorker',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('employee_no', fields.CharField(description='工号', max_length=100)),
                ('trade', fields.CharField(description='工种', max_length=100)),
                ('name', fields.CharField(description='姓名', max_length=100)),
                ('remark', fields.TextField(null=True, description='备注', unique=False)),
            ],
            options={'table': 'biz_labor_management_worker', 'app': 'app_system', 'pk_attr': 'id', 'table_description': '劳务人员'},
            bases=['BaseModel', 'AuditMixin'],
        ),
    ]
