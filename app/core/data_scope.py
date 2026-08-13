"""
行级数据权限（数据范围过滤）。

角色的 ``data_scope`` 字段控制该角色能看到的数据范围：

    - ``all``        — 全部数据（无过滤）
    - ``scope``      — 仅当前业务范围数据（可映射为租户/组织/项目等）
    - ``self``       — 仅本人数据
    - ``custom``     — 自定义（预留，当前降级到 self）

多角色取最宽松：all > scope > self。超级管理员自动跳过。

用法示例::

    from app.core.data_scope import build_scope_filter, get_current_data_scope

    scope = await get_current_data_scope(redis)
    scope_q = build_scope_filter(
        scope=scope,
        user_id=CTX_USER_ID.get(),
        scope_id=get_current_scope_id(),
        scope_id_field="tenant_id",
    )
    total, products = await controller.list(..., search=q & scope_q)
"""

from __future__ import annotations

from enum import Enum

from tortoise.expressions import Q

from app.core.ctx import CTX_ROLE_CODES, is_super_admin

# 数据范围宽松度排序（用于多角色取最宽松）
_SCOPE_PRIORITY = {"all": 0, "scope": 1, "self": 2, "custom": 3}


class DataScopeType(str, Enum):
    """数据权限范围枚举"""

    all = "all"
    scope = "scope"
    self_ = "self"
    custom = "custom"


def build_scope_filter(
    *,
    scope: str,
    user_id: int | None = None,
    scope_id: int | None = None,
    user_id_field: str = "user_id",
    scope_id_field: str = "scope_id",
) -> Q:
    """根据数据范围构建 Tortoise Q 过滤条件。

    超级管理员和 ``scope="all"`` 返回空 Q（不过滤）。

    Args:
        scope: 数据范围值（all / scope / self / custom）。
        user_id: 当前用户 ID。
        scope_id: 当前用户所属业务范围 ID，例如租户/组织/项目。
        user_id_field: 模型中用户 ID 字段名。
        scope_id_field: 模型中业务范围字段名。
    """
    if is_super_admin() or scope == DataScopeType.all:
        return Q()
    if scope == DataScopeType.scope and scope_id is not None:
        return Q(**{scope_id_field: scope_id})  # type: ignore[arg-type]
    # self / custom fallback — 仅看自己的数据
    if user_id is not None:
        return Q(**{user_id_field: user_id})  # type: ignore[arg-type]
    return Q()


async def get_current_data_scope(redis) -> str:
    """获取当前用户最宽松角色的 data_scope。

    遍历 ``CTX_ROLE_CODES``，从 Redis 读取每个角色的 ``data_scope``，
    返回最宽松（优先级最高）的值。

    Args:
        redis: Redis 实例。为 None 时回退到数据库查询。
    """
    if is_super_admin():
        return DataScopeType.all

    role_codes = CTX_ROLE_CODES.get()
    if not role_codes:
        return DataScopeType.self_

    best_scope = DataScopeType.self_
    best_priority = _SCOPE_PRIORITY.get(best_scope, 99)

    if redis:
        for code in role_codes:
            raw = await redis.get(f"role:{code}:data_scope")
            if raw:
                scope_val = raw if isinstance(raw, str) else raw.decode()
                priority = _SCOPE_PRIORITY.get(scope_val, 99)
                if priority < best_priority:
                    best_scope = scope_val
                    best_priority = priority
                    if best_priority == 0:
                        break
    else:
        # Redis 不可用时回退到数据库
        from app.system.models.admin import Role, StatusType

        roles = await Role.filter(role_code__in=role_codes, status_type=StatusType.enable).values_list("data_scope", flat=True)  # type: ignore[misc]
        for scope_val in roles:
            val = scope_val.value if hasattr(scope_val, "value") else str(scope_val)  # type: ignore[union-attr]
            priority = _SCOPE_PRIORITY.get(val, 99)
            if priority < best_priority:
                best_scope = val
                best_priority = priority

    return best_scope
