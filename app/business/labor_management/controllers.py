"""
labor_management controllers — 基于 CRUDBase 的控制器。
"""

from app.business.labor_management.models import LaborProject, LaborReceipt, LaborWorker, LaborWorkHour
from app.utils import CRUDBase

labor_project_controller = CRUDBase(model=LaborProject)
labor_receipt_controller = CRUDBase(model=LaborReceipt)
labor_worker_controller = CRUDBase(model=LaborWorker)
labor_work_hour_controller = CRUDBase(model=LaborWorkHour)
