from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('app_system', '0016_auto_20261122_1420')]

    initial = False

    operations = [
        ops.AddField(
            model_name='LaborProject',
            name='skip_painting',
            field=fields.BooleanField(default=False, description='无需刷漆', db_default=False),
        ),
    ]
