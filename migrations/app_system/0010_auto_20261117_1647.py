from tortoise import migrations
from tortoise.migrations import operations as ops
from app.business.work_ticket_management.models import TicketCodeSource
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0009_auto_20261117_1328')]

    initial = False

    operations = [
        ops.CreateModel(
            name='WorkProject',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('owner_id', fields.IntField(description='资产所属账号')),
                ('part_no', fields.CharField(description='项目号', max_length=200)),
            ],
            options={'table': 'biz_work_ticket_management_project', 'app': 'app_system', 'unique_together': (('owner_id', 'part_no'),), 'pk_attr': 'id', 'table_description': '项目资产'},
            bases=['BaseModel', 'AuditMixin'],
        ),
        ops.CreateModel(
            name='WorkProjectOrder',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('project', fields.ForeignKeyField('app_system.WorkProject', source_field='project_id', description='项目', db_constraint=True, to_field='id', related_name='asset_orders', on_delete=OnDelete.RESTRICT)),
                ('order', fields.ForeignKeyField('app_system.Order', source_field='order_id', null=True, description='来源订单', db_constraint=True, to_field='id', related_name='work_project_assets', on_delete=OnDelete.SET_NULL)),
                ('order_no', fields.CharField(description='订单号', max_length=100)),
                ('name', fields.CharField(description='订单名称', max_length=200)),
            ],
            options={'table': 'biz_work_ticket_management_project_order', 'app': 'app_system', 'unique_together': (('project', 'order_no'),), 'pk_attr': 'id', 'table_description': '项目订单资产'},
            bases=['BaseModel', 'AuditMixin'],
        ),
        ops.CreateModel(
            name='WorkAssetTicket',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('project_order', fields.ForeignKeyField('app_system.WorkProjectOrder', source_field='project_order_id', description='项目订单', db_constraint=True, to_field='id', related_name='asset_tickets', on_delete=OnDelete.RESTRICT)),
                ('ticket_code', fields.CharField(description='外部工票码', max_length=100)),
                ('ticket_code_key', fields.CharField(description='工票码比较键', max_length=100)),
                ('code_source', fields.CharEnumField(default=TicketCodeSource.manual, description='工票码来源', enum_type=TicketCodeSource, max_length=10)),
                ('total_hours', fields.DecimalField(null=True, description='工票总工时', max_digits=7, decimal_places=2)),
            ],
            options={'table': 'biz_work_ticket_management_asset_ticket', 'app': 'app_system', 'unique_together': (('project_order', 'ticket_code_key'),), 'pk_attr': 'id', 'table_description': '订单工票'},
            bases=['BaseModel', 'AuditMixin'],
        ),
        ops.CreateModel(
            name='WorkAssetAllocation',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('ticket', fields.ForeignKeyField('app_system.WorkAssetTicket', source_field='ticket_id', description='工票', db_constraint=True, to_field='id', related_name='allocations', on_delete=OnDelete.RESTRICT)),
                ('worker', fields.ForeignKeyField('app_system.Worker', source_field='worker_id', description='人员', db_constraint=True, to_field='id', related_name='asset_allocations', on_delete=OnDelete.RESTRICT)),
                ('assigned_on', fields.DateField(db_index=True, description='分配日期')),
                ('hours', fields.DecimalField(null=True, description='分配工时', max_digits=7, decimal_places=2)),
            ],
            options={'table': 'biz_work_ticket_management_asset_allocation', 'app': 'app_system', 'unique_together': (('ticket', 'worker', 'assigned_on'),), 'pk_attr': 'id', 'table_description': '工票人员分配与工时'},
            bases=['BaseModel', 'AuditMixin'],
        ),
    ]
