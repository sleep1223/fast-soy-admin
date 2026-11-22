"""
labor_management controllers — 基于 CRUDBase 的控制器。
"""

from typing import Any

from pydantic import BaseModel
from tortoise.expressions import Q

from app.business.labor_management.models import LaborProject, LaborWorker, LaborWorkHour
from app.business.labor_management.schemas import LaborWorkHourCreate, LaborWorkHourUpdate
from app.utils import CRUDBase

labor_project_controller = CRUDBase(model=LaborProject)
labor_worker_controller = CRUDBase(model=LaborWorker)


class LaborWorkHourController(CRUDBase[LaborWorkHour, LaborWorkHourCreate, LaborWorkHourUpdate]):
    """工票列表和导出共用分配状态筛选。"""

    def build_search(self, obj_in: BaseModel, *args: Any, **kwargs: Any) -> Q:
        query = super().build_search(obj_in, *args, **kwargs)
        assigned = getattr(obj_in, "is_assigned", None)
        if assigned is True:
            query &= Q(allocation_month__isnull=False) & Q(worker_id__isnull=False)
        elif assigned is False:
            query &= Q(allocation_month__isnull=True) | Q(worker_id__isnull=True)
        order_nos = getattr(obj_in, "order_nos", None)
        if order_nos is not None:
            query &= Q(order_no__in=order_nos)
        return query


labor_work_hour_controller = LaborWorkHourController(model=LaborWorkHour)
