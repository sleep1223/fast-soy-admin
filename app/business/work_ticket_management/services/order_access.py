"""Read-only access to the registered Order model without importing its module."""

from __future__ import annotations

from typing import Any, cast

from tortoise import Tortoise
from tortoise.backends.base.client import BaseDBAsyncClient

from app.business.work_ticket_management.rules import OrderSnapshot


def order_model() -> type[Any]:
    """Resolve Order through the Tortoise registry, preserving module boundaries."""
    return cast(type[Any], Tortoise.apps["app_system"]["Order"])


async def get_order(order_id: int, db: BaseDBAsyncClient) -> Any | None:
    return await order_model().filter(id=order_id).using_db(db).first()


def order_snapshot(order: Any) -> OrderSnapshot:
    return OrderSnapshot(
        order_no=str(getattr(order, "order_no", "") or ""),
        part_no=str(getattr(order, "part_no", "") or ""),
        name=str(getattr(order, "name", "") or ""),
        net_weight=getattr(order, "net_weight", None),
        gross_weight=getattr(order, "gross_weight", None),
        process_route=getattr(order, "process_route", None),
        quantity=getattr(order, "quantity", None),
        received_quantity=getattr(order, "received_quantity", None),
    )


def order_values(order: Any) -> dict[str, Any]:
    snapshot = order_snapshot(order)
    return {
        "order_no_snapshot": snapshot.order_no or None,
        "part_no_snapshot": snapshot.part_no or None,
        "name_snapshot": snapshot.name or None,
    }
