from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0013_auto_20261122_0924')]

    initial = False

    operations = [
        ops.CreateModel(
            name='LaborReceipt',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('receipt_month', fields.DateField(db_index=True, description='接收月份')),
                ('part_no', fields.CharField(db_index=True, description='项目号', max_length=200)),
            ],
            options={'table': 'biz_labor_management_receipt', 'app': 'app_system', 'unique_together': (('receipt_month', 'part_no'),), 'pk_attr': 'id', 'table_description': '月度接收工件明细'},
            bases=['BaseModel', 'AuditMixin'],
        ),
        ops.AddField(
            model_name='LaborWorkHour',
            name='allocation_month',
            field=fields.DateField(null=True, db_index=True, description='分配月份'),
        ),
        ops.AddField(
            model_name='LaborWorkHour',
            name='receipt',
            field=fields.ForeignKeyField('app_system.LaborReceipt', source_field='receipt_id', null=True, description='接收工件明细', db_constraint=True, to_field='id', related_name='work_hours', on_delete=OnDelete.RESTRICT),
        ),
    ]
