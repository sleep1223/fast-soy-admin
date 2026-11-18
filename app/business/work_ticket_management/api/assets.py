"""项目资产工作台 API。"""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.business.work_ticket_management import constants
from app.business.work_ticket_management.api.common import dump, page
from app.business.work_ticket_management.api.imports import parse_options, read_excel_file
from app.business.work_ticket_management.schemas_assets import (
    WorkAssetAllocationCreate,
    WorkAssetAllocationUpdate,
    WorkAssetReportSearch,
    WorkAssetTicketCreate,
    WorkProjectSearch,
)
from app.business.work_ticket_management.services import assets
from app.utils import PageQueryBase, SqidPath, Success, SuccessExtra, encode_id, get_current_user_id, require_buttons

router = APIRouter(tags=["工时资产"])
IMPORT_PERMISSION = require_buttons(constants.B_IMPORT_PLAN)
TICKET_PERMISSION = require_buttons(constants.B_TICKET_CREATE)
ALLOCATION_PERMISSION = require_buttons(constants.B_TIME_EDIT)


@router.post("/work_projects/search", summary="查询我的项目", name="work_ticket_management.work_projects.list")
async def search_projects(obj_in: WorkProjectSearch) -> SuccessExtra:
    total, rows = await assets.list_projects(get_current_user_id(), obj_in)
    return page(rows, total, obj_in.current, obj_in.size)


@router.post("/work_projects/import-preview", summary="预览项目 Excel", name="work_ticket_management.work_projects.import_preview", dependencies=[IMPORT_PERMISSION])
async def preview_projects(file: Annotated[UploadFile, File()], options: Annotated[str | None, Form()] = None) -> Success:
    parsed = await assets.parse_project_excel(await read_excel_file(file), parse_options(options))
    return Success(data=dump(parsed.preview))


@router.post("/work_projects/import", summary="导入项目并匹配全部现有订单", name="work_ticket_management.work_projects.import", dependencies=[IMPORT_PERMISSION])
async def import_projects(file: Annotated[UploadFile, File()], options: Annotated[str | None, Form()] = None) -> Success:
    parsed = await assets.parse_project_excel(await read_excel_file(file), parse_options(options))
    return Success(data=dump(await assets.import_projects(get_current_user_id(), parsed)))


@router.post("/work_projects/{project_id}/orders/search", summary="查询项目订单", name="work_ticket_management.work_project_orders.list")
async def search_orders(project_id: SqidPath, obj_in: PageQueryBase) -> SuccessExtra:
    total, rows = await assets.list_orders(get_current_user_id(), project_id, obj_in)
    return page(rows, total, obj_in.current, obj_in.size)


@router.get("/work_project_orders/{order_id}/tickets", summary="查看订单工票及人员分配", name="work_ticket_management.work_asset_tickets.list")
async def list_tickets(order_id: SqidPath) -> Success:
    return Success(data=dump(await assets.list_tickets(get_current_user_id(), order_id)))


@router.post("/work_project_orders/{order_id}/tickets", summary="登记订单工票", name="work_ticket_management.work_asset_tickets.create", dependencies=[TICKET_PERMISSION])
async def create_ticket(order_id: SqidPath, obj_in: WorkAssetTicketCreate) -> Success:
    item_id = await assets.save_ticket(get_current_user_id(), order_id, obj_in)
    return Success(data=encode_id(item_id))


@router.put("/work_asset_tickets/{ticket_id}", summary="更新工票登记", name="work_ticket_management.work_asset_tickets.update", dependencies=[TICKET_PERMISSION])
async def update_ticket(ticket_id: SqidPath, obj_in: WorkAssetTicketCreate) -> Success:
    await assets.save_ticket(get_current_user_id(), ticket_id, obj_in, editing=True)
    return Success()


@router.post("/work_asset_tickets/{ticket_id}/allocations", summary="分配工票人员及工时", name="work_ticket_management.work_asset_allocations.create", dependencies=[ALLOCATION_PERMISSION])
async def create_allocation(ticket_id: SqidPath, obj_in: WorkAssetAllocationCreate) -> Success:
    item_id = await assets.save_allocation(get_current_user_id(), ticket_id, obj_in)
    return Success(data=encode_id(item_id))


@router.put(
    "/work_asset_tickets/{ticket_id}/allocations/{allocation_id}",
    summary="调整分配人员、日期及工时",
    name="work_ticket_management.work_asset_allocations.update",
    dependencies=[ALLOCATION_PERMISSION],
)
async def update_allocation(ticket_id: SqidPath, allocation_id: SqidPath, obj_in: WorkAssetAllocationUpdate) -> Success:
    await assets.save_allocation(get_current_user_id(), ticket_id, obj_in, allocation_id=allocation_id)
    return Success()


@router.post("/work_asset_allocations/report", summary="按日期和生产单位统计已分配工时", name="work_ticket_management.work_asset_allocations.report")
async def report(obj_in: WorkAssetReportSearch) -> Success:
    return Success(data=dump(await assets.report(get_current_user_id(), obj_in)))
