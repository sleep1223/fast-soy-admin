from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0017_auto_20261122_1505')]

    initial = False

    operations = [
        ops.AddField(
            model_name='LaborProject',
            name='imported_at',
            field=fields.DatetimeField(null=True, description='首次导入时间', auto_now=False, auto_now_add=False),
        ),
    ]
