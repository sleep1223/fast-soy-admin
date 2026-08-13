"""
轻量级状态机 — 校验状态流转合法性 + 原子更新 + 审计日志。

不引入独立的 TransitionLog 表，使用 ``radar_log`` 作为审计记录。

用法示例::

    from app.core.state_machine import StateMachine

    TICKET_FSM = StateMachine(
        transitions={
            "open":        ["processing"],
            "processing":  ["resolved"],
            "resolved":    [],          # 终态
        }
    )

    # 在服务层
    await TICKET_FSM.transition(
        obj=ticket,
        to_state="resolved",
        state_field="status",
        actor_id=current_user_id,
        log_fn=radar_log,
    )
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from app.core.code import Code
from app.core.exceptions import BizError


class TransitionError(BizError):
    """不合法的状态流转。"""


class StateMachine:
    """轻量级状态机。

    ``transitions`` 字典定义允许的状态流转::

        {
            "pending":    ["onboarding"],       # pending → onboarding
            "onboarding": ["active", "pending"], # onboarding → active or back to pending
            "active":     ["resigned"],
            "resigned":   [],                    # 终态
        }
    """

    def __init__(
        self,
        transitions: dict[str, list[str]],
        *,
        error_code: str = Code.STATE_TRANSITION_INVALID,
    ) -> None:
        self.transitions = transitions
        self.error_code = error_code

    def allowed(self, from_state: str, to_state: str) -> bool:
        """检查 from_state → to_state 是否合法。"""
        return to_state in self.transitions.get(from_state, [])

    def allowed_targets(self, from_state: str) -> list[str]:
        """返回 from_state 可达的所有目标状态。"""
        return list(self.transitions.get(from_state, []))

    async def transition(
        self,
        obj: Any,
        to_state: str,
        state_field: str = "status",
        actor_id: int | None = None,
        log_fn: Callable[..., None] | None = None,
        extra_updates: dict[str, Any] | None = None,
    ) -> None:
        """执行状态流转。

        1. 读取当前状态（兼容 Enum.value）
        2. 校验 ``allowed()``，不合法抛 ``TransitionError``
        3. ``update_from_dict`` + ``save``
        4. 调用 ``log_fn`` 记录变更

        Args:
            obj: Tortoise 模型实例。
            to_state: 目标状态值。
            state_field: 模型中存储状态的字段名（默认 ``"status"``）。
            actor_id: 操作人 ID（用于日志）。
            log_fn: 日志函数，签名 ``log_fn(message, *, data={...})``。
                推荐传入 ``radar_log``。
            extra_updates: 与状态变更同时原子更新的额外字段。

        Raises:
            TransitionError: 当前状态不允许转换到目标状态。
        """
        current = getattr(obj, state_field)
        from_state = current.value if hasattr(current, "value") else str(current)

        if not self.allowed(from_state, to_state):
            raise TransitionError(
                code=self.error_code,
                msg=f"不允许从 '{from_state}' 转换为 '{to_state}'，允许的目标: {self.allowed_targets(from_state)}",
            )

        updates: dict[str, Any] = {state_field: to_state, **(extra_updates or {})}
        obj = obj.update_from_dict(updates)
        await obj.save(update_fields=list(updates.keys()))

        if log_fn:
            log_fn(
                "状态变更",
                data={
                    "model": obj.__class__.__name__,
                    "id": obj.pk,
                    "fromState": from_state,
                    "toState": to_state,
                    "actorId": actor_id,
                    "at": datetime.now(tz=timezone.utc).isoformat(),
                },
            )
