from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.api.v1.utils import refresh_api_list, insert_log
from app.controllers import user_controller
from app.controllers.api import api_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth, DependPermission
from app.models.system import Api, Role
from app.models.system import LogType, LogDetailType
from app.schemas.base import Success, SuccessExtra
from app.schemas.apis import ApiCreate, ApiUpdate

router = APIRouter()


@router.get("/apis", summary="查看API列表", dependencies=[DependAuth])
async def _(
        current: int = Query(1, description="页码"),
        size: int = Query(10, description="每页数量"),
        path: str = Query(None, description="API路径"),
        summary: str = Query(None, description="API简介"),
        tags: str = Query(None, description="API模块"),
        status: str = Query(None, description="API状态"),
):
    q = Q()
    if path:
        q &= Q(path__contains=path)
    if summary:
        q &= Q(summary__contains=summary)
    if tags:
        q &= Q(tags__contains=tags.split("|"))
    if status:
        q &= Q(status__contains=status)

    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    user_role_objs: list[Role] = await user_obj.roles
    user_role_codes = [role_obj.role_code for role_obj in user_role_objs]
    if "R_SUPER" in user_role_codes:
        total, api_objs = await api_controller.list(page=current, page_size=size, search=q, order=["tags", "id"])
    else:
        api_objs: list[Api] = []
        for role_obj in user_role_objs:
            api_objs.extend([api_obj for api_obj in await role_obj.apis])

        unique_apis = list(set(api_objs))
        sorted_menus = sorted(unique_apis, key=lambda x: x.id)
        # 实现分页
        start = (current - 1) * size
        end = start + size
        api_objs = sorted_menus[start:end]
        total = len(sorted_menus)

    records = []
    for obj in api_objs:
        data = await obj.to_dict(exclude_fields=["create_time", "update_time"])
        data["tags"] = "|".join(data["tags"])
        records.append(data)
    data = {"records": records}
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiGetList, by_user_id=user_obj.id)
    return SuccessExtra(data=data, total=total, current=current, size=size)


@router.get("/apis/{api_id}", summary="查看API", dependencies=[DependPermission])
async def _(api_id: int):
    api_obj = await api_controller.get(id=api_id)
    data = await api_obj.to_dict(exclude_fields=["id", "create_time", "update_time"])
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiGetOne, by_user_id=0)
    return Success(data=data)


def build_api_tree(apis: list[Api]):
    parent_map = {"root": {"id": "root", "children": []}}
    # 遍历输入数据
    for api in apis:
        tags = api.tags
        parent_id = "root"
        for tag in tags:
            node_id = f"parent${tag}"
            # 如果当前节点不存在，则创建一个新的节点
            if node_id not in parent_map:
                node = {"id": node_id, "summary": tag, "children": []}
                parent_map[node_id] = node
                parent_map[parent_id]["children"].append(node)
            parent_id = node_id
        parent_map[parent_id]["children"].append({
            "id": api.id,
            "summary": api.summary,
        })
    return parent_map["root"]["children"]


@router.get("/apis/tree/", summary="查看API树", dependencies=[DependPermission])
async def _():
    api_objs = await Api.all()
    data = []
    if api_objs:
        data = build_api_tree(api_objs)
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiGetTree, by_user_id=0)
    return Success(data=data)


@router.post("/apis", summary="创建API", dependencies=[DependPermission])
async def _(
        api_in: ApiCreate,
):
    if isinstance(api_in.tags, str):
        api_in.tags = api_in.tags.split("|")
    new_api = await api_controller.create(obj_in=api_in)
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiCreateOne, by_user_id=0)
    return Success(msg="Created Successfully", data={"created_id": new_api.id})


@router.patch("/apis/{api_id}", summary="更新API", dependencies=[DependPermission])
async def _(
        api_id: int,
        api_in: ApiUpdate,
):
    if isinstance(api_in.tags, str):
        api_in.tags = api_in.tags.split("|")
    await api_controller.update(id=api_id, obj_in=api_in)
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiUpdateOne, by_user_id=0)
    return Success(msg="Update Successfully", data={"updated_id": api_id})


@router.delete("/apis/{api_id}", summary="删除API", dependencies=[DependPermission])
async def _(
        api_id: int,
):
    await api_controller.remove(id=api_id)
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiDeleteOne, by_user_id=0)
    return Success(msg="Deleted Successfully", data={"deleted_id": api_id})


@router.delete("/apis", summary="批量删除API", dependencies=[DependPermission])
async def _(ids: str = Query(..., description="API ID列表, 用逗号隔开")):
    api_ids = ids.split(",")
    deleted_ids = []
    for api_id in api_ids:
        api_obj = await Api.get(id=int(api_id))
        await api_obj.delete()
        deleted_ids.append(int(api_id))
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiBatchDelete, by_user_id=0)
    return Success(msg="Deleted Successfully", data={"deleted_ids": deleted_ids})


@router.post("/apis/refresh/", summary="刷新API列表", dependencies=[DependPermission])
async def _():
    await refresh_api_list()
    await insert_log(log_type=LogType.UserLog, log_detail_type=LogDetailType.ApiRefresh, by_user_id=0)
    return Success()
