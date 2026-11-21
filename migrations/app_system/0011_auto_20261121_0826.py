from tortoise import migrations
from tortoise.migrations import operations as ops

class Migration(migrations.Migration):
    dependencies = [('app_system', '0010_auto_20261117_1647')]

    initial = False

    operations = [
        ops.DeleteModel(name='WorkAssetAllocation'),
        ops.DeleteModel(name='WorkAssetTicket'),
        ops.DeleteModel(name='WorkProjectOrder'),
        ops.DeleteModel(name='WorkProject'),
        ops.DeleteModel(name='WorkTimeEntry'),
        ops.DeleteModel(name='WorkTicketAssignment'),
        ops.DeleteModel(name='WorkTicket'),
        ops.RemoveField(model_name='MonthlyImportRow', name='duplicate_of_row'),
        ops.DeleteModel(name='MonthlyImportRow'),
        ops.DeleteModel(name='MonthlyImportBatch'),
        ops.DeleteModel(name='WorkMonthStatusLog'),
        ops.DeleteModel(name='WorkMonth'),
        ops.DeleteModel(name='OrderUnitMapping'),
        ops.DeleteModel(name='Worker'),
        ops.DeleteModel(name='ProductionUnit'),
    ]
