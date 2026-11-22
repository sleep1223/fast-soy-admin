from tortoise import migrations
from tortoise.migrations import operations as ops

class Migration(migrations.Migration):
    dependencies = [('app_system', '0014_auto_20261122_0937')]

    initial = False

    operations = [
        ops.RemoveField(model_name='LaborWorkHour', name='receipt'),
        ops.DeleteModel(name='LaborProject'),
        ops.DeleteModel(name='LaborReceipt'),
    ]
