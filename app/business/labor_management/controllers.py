"""
labor_management controllers — 基于 CRUDBase 的控制器。
"""

from app.business.labor_management.models import LaborWorker, LaborWorkHour
from app.utils import CRUDBase

labor_worker_controller = CRUDBase(model=LaborWorker)
labor_work_hour_controller = CRUDBase(model=LaborWorkHour)
