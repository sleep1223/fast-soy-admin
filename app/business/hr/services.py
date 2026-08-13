"""
HR service — 员工入职、部门主管任命、标签管理、状态流转的核心业务逻辑。
"""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from tortoise.expressions import Q
from tortoise.functions import Count
from tortoise.transactions import in_transaction

from app.business.hr.config import BIZ_SETTINGS
from app.business.hr.controllers import department_controller, employee_controller, status_log_controller, tag_controller
from app.business.hr.events import HR_EMPLOYEE_CREATED, HR_EMPLOYEE_STATUS_CHANGED, HR_EMPLOYEE_UPDATED
from app.business.hr.models import Department, Employee, EmployeeStatus, Tag
from app.business.hr.schemas import EmployeeCreate, EmployeeDepartmentTransfer, EmployeeSearch, EmployeeUpdate
from app.business.hr.serializers import employee_record
from app.utils import (
    BizError,
    Code,
    Fail,
    StateMachine,
    StatusType,
    Success,
    assert_object_policy,
    create_system_user,
    emit,
    get_current_user_id,
    get_db_conn,
    grant_user_role_code,
    invalidate_user_session,
    radar_log,
    revoke_user_role_code,
)

DEPT_MANAGER_ROLE = "R_DEPT_MGR"
EMPLOYEE_ROLE = "R_EMPLOYEE"
ACTIVE_EMPLOYEE_STATUSES = [EmployeeStatus.probation, EmployeeStatus.active]


# ---- 员工状态机 ----

EMPLOYEE_FSM = StateMachine(
    transitions={
        "probation": ["active", "resigned"],
        "active": ["resigned"],
        "resigned": ["probation"],
    },
    error_code=Code.HR_INVALID_TRANSITION,
)


def _actor_id() -> int | None:
    try:
        return get_current_user_id()
    except LookupError:
        return None


def _state_value(status: EmployeeStatus | str) -> str:
    return status.value if isinstance(status, EmployeeStatus) else str(status)


async def generate_employee_no() -> str:
    """生成工号: 前缀 + 自增序号"""
    count = await employee_controller.model.all().count()
    return f"{BIZ_SETTINGS.EMPLOYEE_NO_PREFIX}{count + 1:04d}"


async def _record_status_log(emp: Employee, from_state: str | None, to_state: str, remark: str | None) -> None:
    await status_log_controller.create({
        "employee_id": emp.id,
        "from_status": from_state,
        "to_status": to_state,
        "remark": remark,
        "operated_by": _actor_id(),
    })


async def _transition_status(emp: Employee, to_state: EmployeeStatus, *, remark: str | None = None) -> None:
    from_state = _state_value(emp.status)
    to_state_value = _state_value(to_state)
    await EMPLOYEE_FSM.transition(
        obj=emp,
        to_state=to_state_value,
        state_field="status",
        actor_id=_actor_id(),
        log_fn=radar_log,
    )
    await _record_status_log(emp, from_state, to_state_value, remark)
    await emit(HR_EMPLOYEE_STATUS_CHANGED, employee_id=emp.id, from_state=from_state, to_state=to_state_value)


async def _get_active_employee(emp_id: int) -> Employee | None:
    return await Employee.filter(id=emp_id, status__in=ACTIVE_EMPLOYEE_STATUSES).select_related("department", "user").first()


async def _get_employee_user(emp: Employee):
    await emp.fetch_related("user")
    return getattr(emp, "user", None)


async def _grant_department_manager_role(redis: Redis, emp: Employee) -> None:
    user = await _get_employee_user(emp)
    if user:
        await grant_user_role_code(redis, user, DEPT_MANAGER_ROLE)


async def _revoke_department_manager_role_if_unused(redis: Redis, emp: Employee) -> None:
    if await Department.filter(manager_id=emp.id).exists():
        return
    user = await _get_employee_user(emp)
    if user:
        await revoke_user_role_code(redis, user, DEPT_MANAGER_ROLE)


async def _replace_managed_departments(redis: Redis, emp: Employee, new_manager_employee_id: int | None) -> None:
    """Transfer departments managed by emp before emp leaves or moves departments."""
    managed_departments = await Department.filter(manager_id=emp.id).all()
    if not managed_departments:
        return

    if not new_manager_employee_id:
        raise BizError(code=Code.FAIL, msg="该员工是部门主管，请先指定接任主管")

    if len(managed_departments) > 1:
        raise BizError(code=Code.FAIL, msg="该员工管理多个部门，请先逐个调整部门主管")

    dept = managed_departments[0]
    replacement = await _get_active_employee(new_manager_employee_id)
    if not replacement or replacement.department_id != dept.id or replacement.id == emp.id:
        raise BizError(code=Code.FAIL, msg="接任主管必须是原部门内待转正或在职员工")

    await Department.filter(id=dept.id).update(manager_id=replacement.id)
    await _grant_department_manager_role(redis, replacement)
    await _revoke_department_manager_role_if_unused(redis, emp)


async def create_employee(emp_in: EmployeeCreate, redis: Redis):
    """HR 视角办理入职 — 必须指定部门，自动创建系统用户并绑定 R_EMPLOYEE。"""
    if not await Department.filter(id=emp_in.department_id, status=StatusType.enable).exists():
        return Fail(code=Code.HR_DEPARTMENT_REQUIRED, msg="创建员工需要指定有效部门")

    employee_no = await generate_employee_no()

    async with in_transaction(get_db_conn(Employee)):
        try:
            result = await create_system_user(
                redis,
                user_name=emp_in.user_name,
                nick_name=emp_in.name,
                user_email=emp_in.email,
                user_gender=emp_in.user_gender,
                user_phone=emp_in.phone,
                role_codes=[EMPLOYEE_ROLE],
            )
        except ValueError as e:
            return Fail(msg=str(e))

        emp_data = emp_in.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={"user_name", "user_gender", "status"},
        )
        emp_data.update(employee_no=employee_no, user_id=result.user.id, status=EmployeeStatus.probation)
        new_emp = await employee_controller.create(obj_in=emp_data)

    radar_log("办理员工入职", data={"employeeId": new_emp.id, "employeeNo": employee_no, "userId": result.user.id})
    await emit(HR_EMPLOYEE_CREATED, employee_id=new_emp.id, employee_no=employee_no)
    return Success(
        msg="创建成功",
        data={
            "employee_id": new_emp.id,
            "employee_no": employee_no,
            "user_id": result.user.id,
            "raw_password": result.raw_password,
        },
    )


def build_employee_list_query(search_in: EmployeeSearch) -> Q:
    """Build the base employee list query before row-level data scope is applied."""
    q = employee_controller.build_search(search_in, contains_fields=["name", "email"], exact_fields=["status"], range_fields=["created_at"])
    if search_in.department_id:
        q &= Q(department_id=search_in.department_id)
    return q


async def list_employees_with_relations(search_in: EmployeeSearch, *, search: Q | None = None):
    """员工分页列表 — 使用 select_related/prefetch_related 优化 N+1 查询。"""
    q = search if search is not None else build_employee_list_query(search_in)
    total, employees = await employee_controller.list(
        page=search_in.current,
        page_size=search_in.size,
        search=q,
        order=["id"],
        select_related=["department"],
        prefetch_related=["tags"],
    )
    records = []
    for emp in employees:
        records.append(await employee_record(emp, department_name=True, tag_ids=True, tag_names=True))
    return total, records


async def update_employee(emp_id: int, emp_in: EmployeeUpdate):
    """HR 编辑员工基础资料；部门调整、标签和状态分别走独立动作。"""
    target = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", target, module="hr")

    update_data = emp_in.model_dump(
        exclude_unset=True,
        exclude={"department_id", "status", "tag_ids"},
    )
    if update_data:
        await employee_controller.update(id=emp_id, obj_in=update_data)
        user = await _get_employee_user(target)
        if user:
            user_updates: dict[str, Any] = {}
            if "name" in update_data:
                user_updates["nick_name"] = update_data["name"]
            if "email" in update_data:
                user_updates["user_email"] = update_data["email"]
            if "phone" in update_data:
                user_updates["user_phone"] = update_data["phone"]
            if user_updates:
                user.update_from_dict(user_updates)
                await user.save(update_fields=list(user_updates.keys()))

    radar_log("编辑员工基础资料", data={"employeeId": emp_id})
    await emit(HR_EMPLOYEE_UPDATED, employee_id=emp_id)
    return Success(msg="更新成功", data={"updated_id": emp_id})


async def update_employee_tags(emp: Employee, tag_ids: list[int], *, log_label: str = "编辑标签", extra_log: dict[str, object] | None = None):
    """通用标签更新 — 校验上限 + 清除重建 + 日志"""
    if len(tag_ids) > BIZ_SETTINGS.MAX_TAGS_PER_EMPLOYEE:
        return Fail(code=Code.HR_TAGS_EXCEED_LIMIT, msg=f"标签数量不能超过 {BIZ_SETTINGS.MAX_TAGS_PER_EMPLOYEE}")
    await emp.tags.clear()
    for tid in tag_ids:
        await emp.tags.add(await tag_controller.get(id=tid))
    log_data: dict[str, object] = {"employeeId": emp.id, "tagIds": tag_ids}
    if extra_log:
        log_data.update(extra_log)
    radar_log(log_label, data=log_data)
    return Success(msg="标签更新成功")


async def update_managed_employee_tags(emp_id: int, tag_ids: list[int]):
    target = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", target, module="hr")
    return await update_employee_tags(target, tag_ids, log_label="HR编辑员工标签")


async def transfer_employee_department(emp_id: int, body: EmployeeDepartmentTransfer, redis: Redis):
    """HR 调整员工部门；如果目标员工是主管，必须先指定原部门接任主管。"""
    target = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", target, module="hr")
    target_department_id = body.department_id
    if target.department_id == target_department_id:
        return Success(msg="部门未变化", data={"updated_id": emp_id})
    if not await Department.filter(id=target_department_id, status=StatusType.enable).exists():
        return Fail(code=Code.HR_DEPARTMENT_REQUIRED, msg="目标部门不存在或已禁用")

    async with in_transaction(get_db_conn(Employee)):
        await _replace_managed_departments(redis, target, body.new_manager_employee_id)
        await employee_controller.update(id=emp_id, obj_in={"department_id": target_department_id})

    radar_log("调整员工部门", data={"employeeId": emp_id, "departmentId": target_department_id})
    await emit(HR_EMPLOYEE_UPDATED, employee_id=emp_id)
    return Success(msg="部门调整成功", data={"updated_id": emp_id})


async def appoint_department_manager(dept_id: int, manager_id: int | None, redis: Redis):
    """HR 主管任命/移除部门主管。"""
    dept = await department_controller.get(id=dept_id)
    old_manager_id = dept.manager_id
    if old_manager_id == manager_id:
        return Success(msg="主管未变化", data={"updated_id": dept_id})

    new_manager: Employee | None = None
    if manager_id is not None:
        new_manager = await _get_active_employee(manager_id)
        if not new_manager or new_manager.department_id != dept.id:
            return Fail(code=Code.FAIL, msg="部门主管必须是本部门待转正或在职员工")

    await Department.filter(id=dept_id).update(manager_id=manager_id)

    if new_manager:
        await _grant_department_manager_role(redis, new_manager)

    if old_manager_id:
        old_manager = await Employee.filter(id=old_manager_id).select_related("user").first()
        if old_manager:
            await _revoke_department_manager_role_if_unused(redis, old_manager)

    radar_log("调整部门主管", data={"departmentId": dept_id, "managerId": manager_id})
    return Success(msg="主管调整成功", data={"updated_id": dept_id})


async def get_employee_profile(emp: Employee):
    """获取员工完整信息 — 含部门和标签"""
    await emp.fetch_related("department", "tags")
    return await employee_record(emp, department_name=True, tags=True)


async def list_department_employees(department_id: int, exclude_fields: list[str] | None = None):
    """部门员工列表 — 仅返回待转正/在职员工。"""
    employees = await employee_controller.model.filter(department_id=department_id, status__in=ACTIVE_EMPLOYEE_STATUSES).prefetch_related("tags")
    records = []
    for emp in employees:
        records.append(await employee_record(emp, exclude_fields=exclude_fields, tag_names=True))
    return records


async def get_subordinate_or_fail(mgr: Employee, emp_id: int, *, include_self: bool = True) -> Employee:
    """Return an active/probation subordinate in the manager's department or raise a business error."""
    target = await employee_controller.get_or_none(id=emp_id, department_id=mgr.department_id, status__in=ACTIVE_EMPLOYEE_STATUSES)  # type: ignore[attr-defined]
    if not target or (not include_self and target.id == mgr.id):
        raise BizError(code=Code.HR_EMPLOYEE_NOT_IN_DEPT, msg="该员工不在您的部门中")
    return target


async def edit_subordinate_tags(mgr: Employee, emp_id: int, tag_ids: list[int]):
    """主管编辑部门员工标签。"""
    target = await get_subordinate_or_fail(mgr, emp_id)
    return await update_employee_tags(target, tag_ids, log_label="主管编辑下属标签", extra_log={"managerId": mgr.id})


async def regularize_subordinate(mgr: Employee, emp_id: int, remark: str | None = None):
    """部门主管办理本部门员工转正；不能给自己转正。"""
    target = await get_subordinate_or_fail(mgr, emp_id, include_self=False)
    return await regularize_employee(target.id, remark=remark)


async def list_team_employees(mgr: Employee, search_in: EmployeeSearch):
    search_in.department_id = mgr.department_id  # type: ignore[attr-defined]
    q = build_employee_list_query(search_in)
    if search_in.status is None:
        q &= Q(status__in=ACTIVE_EMPLOYEE_STATUSES)
    return await list_employees_with_relations(search_in, search=q)


async def get_team_overview(mgr: Employee):
    """主管视角的部门概览 — 当前团队人数 + 状态分布 + 部门信息。"""
    dept = await Department.get(id=mgr.department_id)  # type: ignore[attr-defined]
    qs = Employee.filter(department_id=mgr.department_id)  # type: ignore[attr-defined]
    total = await qs.filter(status__in=ACTIVE_EMPLOYEE_STATUSES).count()
    status_counts: dict[str, int] = {}

    for status in EmployeeStatus:
        status_counts[status.value] = await qs.filter(status=status).count()
    return {
        "department": {"id": dept.id, "name": dept.name, "code": dept.code},
        "total": total,
        "statusCounts": status_counts,
    }


async def get_public_showcase_overview() -> dict:
    """Public aggregate stats for the HR showcase page."""
    dept_total = await Department.all().count()
    emp_total = await Employee.all().count()
    tag_total = await Tag.all().count()

    status_counts = {status.value: await Employee.filter(status=status).count() for status in EmployeeStatus}
    departments = await Department.all().annotate(employee_count=Count("employees")).order_by("id").values("name", "code", "employee_count")

    return {
        "totals": {
            "department": dept_total,
            "employee": emp_total,
            "tag": tag_total,
        },
        "employeeStatus": status_counts,
        "departments": [
            {
                "name": row["name"],
                "code": row["code"],
                "employeeCount": row["employee_count"],
            }
            for row in departments
        ],
    }


async def regularize_employee(emp_id: int, *, remark: str | None = None):
    """办理转正：待转正 → 在职。"""
    emp = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", emp, module="hr")
    await _transition_status(emp, EmployeeStatus.active, remark=remark)
    return Success(msg="转正成功", data={"employeeId": emp_id, "newState": EmployeeStatus.active.value})


async def resign_employee(emp_id: int, *, remark: str, new_manager_employee_id: int | None, redis: Redis):
    """办理离职：待转正/在职 → 离职，并禁用系统用户、失效 token。"""
    emp = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", emp, module="hr")

    async with in_transaction(get_db_conn(Employee)):
        await _replace_managed_departments(redis, emp, new_manager_employee_id)
        await _transition_status(emp, EmployeeStatus.resigned, remark=remark)
        user = await _get_employee_user(emp)
        if user:
            user.status_type = StatusType.disable
            await user.save(update_fields=["status_type"])
            await invalidate_user_session(redis, user.id)

    radar_log("办理员工离职", data={"employeeId": emp_id})
    return Success(msg="离职成功", data={"employeeId": emp_id, "newState": EmployeeStatus.resigned.value})


async def rehire_employee(emp_id: int, *, remark: str | None, redis: Redis):
    """办理返聘：离职 → 待转正，并启用原系统用户。"""
    emp = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", emp, module="hr")
    user = await _get_employee_user(emp)
    if not user:
        return Fail(code=Code.FAIL, msg="返聘员工必须已绑定系统用户")

    async with in_transaction(get_db_conn(Employee)):
        await _transition_status(emp, EmployeeStatus.probation, remark=remark)
        user.status_type = StatusType.enable
        await user.save(update_fields=["status_type"])

    radar_log("办理员工返聘", data={"employeeId": emp_id, "userId": user.id})
    return Success(msg="返聘成功", data={"employeeId": emp_id, "newState": EmployeeStatus.probation.value})


async def transition_employee(emp_id: int, to_state: EmployeeStatus, *, remark: str | None = None, redis: Redis | None = None):
    """兼容入口：按目标状态分派到显式业务动作。"""
    emp = await employee_controller.get(id=emp_id)
    current = _state_value(emp.status)
    target = _state_value(to_state)
    if current == "probation" and target == "active":
        return await regularize_employee(emp_id, remark=remark)
    if target == "resigned":
        if redis is None:
            raise BizError(code=Code.FAIL, msg="离职操作需要 Redis 上下文")
        if not remark:
            return Fail(code=Code.PARAM_REQUIRED, msg="离职备注不能为空")
        return await resign_employee(emp_id, remark=remark, new_manager_employee_id=None, redis=redis)
    if current == "resigned" and target == "probation":
        if redis is None:
            raise BizError(code=Code.FAIL, msg="返聘操作需要 Redis 上下文")
        return await rehire_employee(emp_id, remark=remark, redis=redis)
    raise BizError(code=Code.HR_INVALID_TRANSITION, msg=f"不允许从 '{current}' 转换为 '{target}'")


async def list_employee_status_logs(emp_id: int):
    emp = await employee_controller.get(id=emp_id)
    await assert_object_policy("hr.employees.update", emp, module="hr")
    logs = await status_log_controller.model.filter(employee_id=emp_id).order_by("-created_at")
    return [await item.to_dict() for item in logs]
