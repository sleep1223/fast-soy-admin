"""
work_ticket_management controllers — 基于 CRUDBase 的控制器。
"""

from app.business.work_ticket_management.models import (
    MonthlyImportBatch,
    MonthlyImportRow,
    OrderUnitMapping,
    ProductionUnit,
    Worker,
    WorkMonth,
    WorkMonthStatusLog,
    WorkTicket,
    WorkTicketAssignment,
    WorkTimeEntry,
)
from app.utils import CRUDBase

production_unit_controller = CRUDBase(model=ProductionUnit)
worker_controller = CRUDBase(model=Worker)
order_unit_mapping_controller = CRUDBase(model=OrderUnitMapping)
work_month_controller = CRUDBase(model=WorkMonth)
monthly_import_batch_controller = CRUDBase(model=MonthlyImportBatch)
monthly_import_row_controller = CRUDBase(model=MonthlyImportRow)
work_ticket_controller = CRUDBase(model=WorkTicket)
work_ticket_assignment_controller = CRUDBase(model=WorkTicketAssignment)
work_time_entry_controller = CRUDBase(model=WorkTimeEntry)
work_month_status_log_controller = CRUDBase(model=WorkMonthStatusLog)
