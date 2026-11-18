"""Asset workbench behavior against an isolated database."""

from datetime import date
from decimal import Decimal

import pytest
from tortoise.context import tortoise_test_context

from app.business.order_management.models import Order
from app.business.work_ticket_management.models import ProductionUnit, Worker, WorkProjectOrder
from app.business.work_ticket_management.schemas_assets import (
    WorkAssetAllocationCreate,
    WorkAssetAllocationUpdate,
    WorkAssetReportSearch,
    WorkAssetTicketCreate,
    WorkProjectSearch,
)
from app.business.work_ticket_management.services import assets
from app.utils import BizError, Code, PageQueryBase, encode_id, write_excel


@pytest.fixture
async def asset_db():
    async with tortoise_test_context(
        modules=["app.business.order_management.models", "app.business.work_ticket_management.models"],
        app_label="app_system",
        connection_label="conn_system",
        use_tz=False,
    ):
        yield


@pytest.mark.asyncio(loop_scope="session")
async def test_excel_import_builds_owned_parent_child_assets_and_is_repeatable(asset_db):
    first_order = await Order.create(order_no="O-1", part_no="0007", name="横梁")
    await Order.create(order_no="O-2", part_no="0007", name="纵梁")
    await Order.create(order_no="IGNORE", part_no="7", name="其他")
    parsed = await assets.parse_project_excel(write_excel(["项目号"], [["0007"], ["0007"], ["LATER"]]), None)
    assert not parsed.preview.errors
    result = await assets.import_projects(1, parsed)
    assert (result.created_count, result.matched_order_count, result.unmatched_project_count) == (2, 2, 1)

    _, (project, unmatched) = await assets.list_projects(1, WorkProjectSearch())
    assert (project.part_no, project.order_count, unmatched.order_count) == ("0007", 2, 0)
    _, orders = await assets.list_orders(1, project.id, PageQueryBase())
    assert [row.order_no for row in orders] == ["O-1", "O-2"]
    with pytest.raises(BizError):
        await assets.list_orders(2, project.id, PageQueryBase())

    await assets.save_ticket(1, orders[0].id, WorkAssetTicketCreate(ticket_code="000009"))
    await first_order.delete()
    await Order.create(order_no="O-3", part_no="0007", name="新增")
    result = await assets.import_projects(1, parsed)
    assert (result.created_count, result.matched_order_count) == (0, 1)
    assert (await assets.list_tickets(1, orders[0].id))[0].ticket_code == "000009"
    assert (await WorkProjectOrder.get(id=orders[0].id)).order_id is None


@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_hours_can_be_held_and_allocated_across_months(asset_db):
    await Order.create(order_no="A-1", part_no="PT-1", name="订单")
    await assets.import_projects(1, await assets.parse_project_excel(write_excel(["件号"], [["PT-1"]]), None))
    _, (project,) = await assets.list_projects(1, WorkProjectSearch())
    _, (order,) = await assets.list_orders(1, project.id, PageQueryBase())
    ticket = await assets.save_ticket(1, order.id, WorkAssetTicketCreate(ticket_code="００１２", code_source="ocr", total_hours=10))
    with pytest.raises(BizError) as error:
        await assets.save_ticket(1, order.id, WorkAssetTicketCreate(ticket_code="0012"))
    assert error.value.code == Code.WORK_TICKET_CODE_CONFLICT

    unit = await ProductionUnit.create(code="U1", name="车间")
    worker = await Worker.create(name="张三", production_unit_id=unit.id)
    worker_id = encode_id(worker.id)
    october = WorkAssetReportSearch(start_date=date(2026, 10, 1), end_date=date(2026, 10, 31))
    november = WorkAssetReportSearch(start_date=date(2026, 11, 1), end_date=date(2026, 11, 30), production_unit_id=encode_id(unit.id))

    held = (await assets.list_tickets(1, order.id))[0]
    assert (held.ticket_code, held.total_hours, held.assigned_hours, held.allocations) == ("0012", 10, 0, [])
    assert not await assets.report(1, october)
    assert WorkAssetAllocationCreate(worker_id=worker_id).assigned_on == date.today()

    initial = WorkAssetAllocationCreate(worker_id=worker_id, assigned_on=date(2026, 10, 31), hours=Decimal("3.25"))
    allocation = await assets.save_allocation(1, ticket, initial)
    with pytest.raises(BizError):
        await assets.save_allocation(2, ticket, initial)
    with pytest.raises(BizError):
        await assets.save_allocation(1, ticket, initial)
    with pytest.raises(BizError):
        await assets.save_allocation(1, ticket, WorkAssetAllocationCreate(worker_id=worker_id, assigned_on=date(2026, 11, 1), hours=7))
    await assets.save_allocation(
        1,
        ticket,
        WorkAssetAllocationUpdate(worker_id=worker_id, assigned_on=date(2026, 11, 1), hours=Decimal("4.25")),
        allocation_id=allocation,
    )
    await assets.save_allocation(1, ticket, WorkAssetAllocationCreate(worker_id=worker_id, assigned_on=date(2026, 11, 2), hours=Decimal("2.35")))
    await assets.save_allocation(1, ticket, WorkAssetAllocationCreate(worker_id=worker_id, assigned_on=date(2026, 10, 30)))
    assert (await assets.report(1, october))[0].hours == 0
    assert not await assets.report(2, november)
    row = (await assets.report(1, november))[0]
    assert (row.worker_name, row.production_unit_name, row.allocation_count, row.hours) == ("张三", "车间", 2, Decimal("6.60"))
    with pytest.raises(BizError):
        await assets.save_ticket(1, ticket, WorkAssetTicketCreate(ticket_code="0012", total_hours=6), editing=True)

    independent_worker = await Worker.create(name="李四")
    await assets.save_allocation(
        1,
        ticket,
        WorkAssetAllocationCreate(worker_id=encode_id(independent_worker.id), assigned_on=date(2026, 11, 1), hours=1),
    )
    all_units = WorkAssetReportSearch(start_date=november.start_date, end_date=november.end_date)
    reported = {item.worker_name: item for item in await assets.report(1, all_units)}
    assert reported["李四"].production_unit_name is None
    assert reported["李四"].hours == 1
    assert (await assets.report(1, november))[0].allocation_count == 2
    detail = (await assets.list_tickets(1, order.id))[0]
    assert (detail.assigned_hours, len(detail.allocations)) == (Decimal("7.60"), 4)
