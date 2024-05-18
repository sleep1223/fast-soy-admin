from datetime import datetime

from fastapi import APIRouter, Query, Depends
from tortoise.expressions import Q

from app.controllers import user_controller
from app.controllers.log import log_controller
from app.core.ctx import CTX_USER_ID
from app.models.system import User, Role, Log, APILog
from app.models.system import LogType
from app.schemas.base import Success, SuccessExtra, Fail
from app.schemas.logs import LogUpdate, LogSearch

router = APIRouter()


@router.get("/logs", summary="查看日志列表")
async def _(log_in: LogSearch = Depends()):
    q = Q()
    if log_in.log_type:
        q &= Q(log_type=log_in.log_type)
    if log_in.log_user and (_by_user := await user_controller.get_by_username(user_name=log_in.log_user)) is not None:
        q &= Q(by_user=_by_user)
    if log_in.log_detail:
        q &= Q(log_detail__contains=log_in.log_detail)
    if log_in.request_url:
        q &= Q(api_log__request_url__contains=log_in.request_url)
    # if log_in.request_data:
    #     q &= Q(api_log__request_data__contains=log_in.request_data)
    # if log_in.response_data:
    #     q &= Q(api_log__response_data__contains=log_in.response_data)
    if log_in.response_code:
        q &= Q(api_log__response_code=log_in.response_code)
    if log_in.time_range:
        _timeRange = log_in.time_range.split(",")
        q &= Q(create_time__gt=datetime.fromtimestamp(int(_timeRange[0]) / 1000), create_time__lt=datetime.fromtimestamp(int(_timeRange[1]) / 1000))

    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    user_role_objs: list[Role] = await user_obj.roles
    user_role_codes = [role_obj.role_code for role_obj in user_role_objs]

    if log_in.log_type is None:
        log_in.log_type = LogType.ApiLog

    if log_in.current is None:
        log_in.current = 1

    if log_in.size is None:
        log_in.size = 10

    if "R_ADMIN" in user_role_codes and log_in.log_type not in [LogType.ApiLog, LogType.UserLog]:  # 管理员只能查看API日志和用户日志
        return Fail(msg="Permission Denied")
    elif "R_SUPER" not in user_role_codes and "R_ADMIN" not in user_role_codes and log_in.log_type != LogType.ApiLog:  # 非超级管理员和管理员只能查看API日志
        return Fail(msg="Permission Denied")

    total, log_objs = await log_controller.list(page=log_in.current, page_size=log_in.size, search=q, order=["-id"])

    records = []
    for obj in log_objs:
        api_log: APILog = await obj.api_log  # type: ignore
        by_user: User = await obj.by_user  # type: ignore
        data = await obj.to_dict(exclude_fields=["by_user_id", "api_log_id"])
        if log_in.log_type == LogType.ApiLog:
            data["requestUrl"] = api_log.request_url
            data["responseCode"] = api_log.response_code
            data["logUser"] = "Request"
        elif log_in.log_type == LogType.SystemLog:
            data["logUser"] = "System"
        else:
            data["logUser"] = by_user.user_name if by_user else "Error"

        records.append(data)
    data = {"records": records}
    return SuccessExtra(data=data, total=total, current=log_in.current, size=log_in.size)


@router.get("/logs/{log_id}", summary="查看日志")
async def _(log_id: int):
    log_obj = await log_controller.get(id=log_id)
    data = await log_obj.to_dict(exclude_fields=["id", "create_time", "update_time"])
    return Success(data=data)


@router.patch("/logs/{log_id}", summary="更新日志")
async def _(
        log_id: int,
        log_in: LogUpdate,
):
    await log_controller.update(id=log_id, obj_in=log_in)
    return Success(msg="Update Successfully")


@router.delete("/logs/{log_id}", summary="删除日志")
async def _(
        log_id: int,
):
    await log_controller.remove(id=log_id)
    return Success(msg="Deleted Successfully", data={"deleted_id": log_id})


@router.delete("/logs", summary="批量删除日志")
async def _(ids: str = Query(..., description="日志ID列表, 用逗号隔开")):
    log_ids = ids.split(",")
    deleted_ids = []
    for log_id in log_ids:
        log_obj = await Log.get(id=int(log_id))
        await log_obj.delete()
        deleted_ids.append(int(log_id))
    return Success(msg="Deleted Successfully", data={"deleted_ids": deleted_ids})
