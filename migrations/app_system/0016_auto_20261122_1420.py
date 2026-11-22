from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0015_auto_20261122_1356')]

    initial = False

    operations = [
        ops.CreateModel(
            name='LaborProject',
            fields=[
                ('created_by', fields.CharField(null=True, description='创建人', max_length=64)),
                ('created_at', fields.DatetimeField(description='创建时间', auto_now=False, auto_now_add=True)),
                ('updated_by', fields.CharField(null=True, description='更新人', max_length=64)),
                ('updated_at', fields.DatetimeField(description='更新时间', auto_now=True, auto_now_add=False)),
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('part_no', fields.CharField(unique=True, description='项目号', max_length=200)),
            ],
            options={'table': 'biz_labor_management_project', 'app': 'app_system', 'pk_attr': 'id', 'table_description': '劳务项目'},
            bases=['BaseModel', 'AuditMixin'],
        ),
    ]
