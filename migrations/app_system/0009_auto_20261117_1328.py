from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0008_auto_20261113_2208')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='Order',
            name='net_weight',
            field=fields.DecimalField(null=True, description='净重', max_digits=16, decimal_places=6),
        ),
        ops.AlterField(
            model_name='WeighingLine',
            name='net_weight',
            field=fields.DecimalField(null=True, description='净重快照', max_digits=16, decimal_places=6),
        ),
    ]
