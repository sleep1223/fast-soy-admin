import logging

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.api.v1.utils import insert_log
from app.controllers.user import user_controller
from app.models.system import LogType, LogDetailType
from app.schemas.base import Success, SuccessExtra
from app.schemas.users import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/users", summary="查看用户列表")
async def _(
        current: int = Query(1, description="页码"),
        size: int = Query(10, description="每页数量"),
        userName: str = Query(None, description="用户名"),
        userGender: str = Query(None, description="用户性别"),
        nickName: str = Query(None, description="用户昵称"),
        userPhone: str = Query(None, description="用户手机"),
        userEmail: str = Query(None, description="用户邮箱"),
        status: str = Query(None, description="用户状态")
):
    q = Q()
    if userName:
        q &= Q(user_name__contains=userName)
    if userGender:
        q &= Q(user_gender__contains=userGender)
    if nickName:
        q &= Q(nick_name__contains=nickName)
    if userPhone:
        q &= Q(user_phone__contains=userPhone)
    if userEmail:
        q &= Q(user_email__contains=userEmail)
    if status:
        q &= Q(status__contains=status)

    total, user_objs = await user_controller.list(page=current, page_size=size, search=q, order=["id"])
    records = []
    for user_obj in user_objs:
        record = await user_obj.to_dict(exclude_fields=["password"])
        await user_obj.fetch_related('roles')
        user_roles = [r.role_code for r in user_obj.roles]
        record.update({"userRoles": user_roles})
        records.append(record)
    data = {"records": records}
    await insert_log(log_type=LogType.AdminLog, log_detail_type=LogDetailType.UserGetList, by_user_id=0)
    return SuccessExtra(data=data, total=total, current=current, size=size)


@router.get("/users/{user_id}", summary="查看用户")
async def get_user(user_id: int):
    user_obj = await user_controller.get(id=user_id)
    await insert_log(log_type=LogType.AdminLog, log_detail_type=LogDetailType.UserGetOne, by_user_id=0)
    return Success(data=await user_obj.to_dict(exclude_fields=["password"]))


@router.post("/users", summary="创建用户")
async def _(user_in: UserCreate):
    # user_obj = await user_controller.get_by_email(user_in.user_email)
    # if user_obj:
    #     raise HTTPException(
    #         code="4090",
    #         msg="The user with this email already exists in the system.",
    #     )
    #
    # if not user_in.roles:
    #     raise HTTPException(
    #         code="4090",
    #         msg="The user must have at least one role that exists.",
    #     )

    new_user = await user_controller.create(obj_in=user_in)
    await user_controller.update_roles_by_code(new_user, user_in.roles)
    await insert_log(log_type=LogType.AdminLog, log_detail_type=LogDetailType.UserCreateOne, by_user_id=0)
    return Success(msg="Created Successfully", data={"created_id": new_user.id})


@router.patch("/users/{user_id}", summary="更新用户")
async def _(user_id: int, user_in: UserUpdate):
    user = await user_controller.update(user_id=user_id, obj_in=user_in)
    # if not user_in.roles:
    #     raise HTTPException(
    #         code="4090",
    #         msg="The user must have at least one role that exists.",
    #     )

    await user_controller.update_roles_by_code(user, user_in.roles)
    await insert_log(log_type=LogType.AdminLog, log_detail_type=LogDetailType.UserUpdateOne, by_user_id=0)
    return Success(msg="Updated Successfully", data={"updated_id": user_id})


@router.delete("/users/{user_id}", summary="删除用户")
async def _(user_id: int):
    await user_controller.remove(id=user_id)
    await insert_log(log_type=LogType.AdminLog, log_detail_type=LogDetailType.UserDeleteOne, by_user_id=0)
    return Success(msg="Deleted Successfully", data={"deleted_id": user_id})


@router.delete("/users", summary="批量删除用户")
async def _(ids: str = Query(..., description="用户ID列表, 用逗号隔开")):
    user_ids = ids.split(",")
    deleted_ids = []
    for user_id in user_ids:
        user_obj = await user_controller.get(id=int(user_id))
        await user_obj.delete()
        deleted_ids.append(int(user_id))

    await insert_log(log_type=LogType.AdminLog, log_detail_type=LogDetailType.UserBatchDeleteOne, by_user_id=0)
    return Success(msg="Deleted Successfully", data={"deleted_ids": deleted_ids})
