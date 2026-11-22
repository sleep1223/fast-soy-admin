"""
order_management controllers — 基于 CRUDBase 的控制器。
"""

from typing import Any

from pydantic import BaseModel
from tortoise.expressions import Q

from app.business.order_management.models import Order
from app.business.order_management.schemas import OrderCreate, OrderUpdate
from app.utils import CRUDBase


class OrderController(CRUDBase[Order, OrderCreate, OrderUpdate]):
    """订单查询支持按一组项目号精确匹配。"""

    def build_search(self, obj_in: BaseModel, *args: Any, **kwargs: Any) -> Q:
        query = super().build_search(obj_in, *args, **kwargs)
        part_nos = getattr(obj_in, "part_nos", None)
        if part_nos is not None:
            query &= Q(part_no__in=part_nos)
        return query


order_controller = OrderController(model=Order)
