"""StateMachine 状态机单元测试。

覆盖点：
- 允许的状态流转成功执行并调用模型保存接口
- 不允许的流转抛出 TransitionError
- 对 Enum 类型当前状态的支持
- 自定义状态字段、错误码、日志函数与 extra_updates
- 终态无目标时 allowed_targets 为空
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pytest

from app.core.code import Code
from app.core.exceptions import BizError
from app.core.state_machine import StateMachine, TransitionError


class FakeStatus(str, Enum):
    pending = "pending"
    active = "active"
    closed = "closed"


@dataclass
class FakeModel:
    id: int = 1
    status: str | FakeStatus = "pending"
    phase: str = "pending"
    closed_at: str | None = None
    _saved_fields: list[str] = field(default_factory=list)
    _save_calls: int = 0

    @property
    def pk(self) -> int:
        return self.id

    def update_from_dict(self, data: dict[str, object]) -> "FakeModel":
        for k, v in data.items():
            setattr(self, k, v)
        return self

    async def save(self, update_fields: list[str] | None = None) -> None:
        self._save_calls += 1
        self._saved_fields = list(update_fields or [])


@pytest.fixture
def order_fsm() -> StateMachine:
    return StateMachine(
        transitions={
            "pending": ["paid", "cancelled"],
            "paid": ["shipped", "refunded"],
            "shipped": ["completed"],
            "completed": [],
            "cancelled": [],
            "refunded": [],
        }
    )


class TestAllowed:
    def test_allowed_returns_true_for_valid_transition(self, order_fsm: StateMachine):
        assert order_fsm.allowed("pending", "paid") is True
        assert order_fsm.allowed("shipped", "completed") is True

    def test_allowed_returns_false_for_invalid_transition(self, order_fsm: StateMachine):
        assert order_fsm.allowed("pending", "completed") is False
        assert order_fsm.allowed("completed", "pending") is False

    def test_allowed_targets(self, order_fsm: StateMachine):
        assert order_fsm.allowed_targets("pending") == ["paid", "cancelled"]
        assert order_fsm.allowed_targets("completed") == []


class TestTransition:
    @pytest.mark.asyncio(loop_scope="session")
    async def test_transition_updates_state_and_calls_log(self, order_fsm: StateMachine):
        obj = FakeModel(status="pending")
        logs: list[dict] = []

        def log_fn(message: str, *, data: dict) -> None:
            logs.append({"message": message, "data": data})

        await order_fsm.transition(
            obj,
            to_state="paid",
            actor_id=42,
            log_fn=log_fn,
        )

        assert obj.status == "paid"
        assert "status" in obj._saved_fields
        assert len(logs) == 1
        assert logs[0]["message"] == "状态变更"
        assert logs[0]["data"]["fromState"] == "pending"
        assert logs[0]["data"]["toState"] == "paid"
        assert logs[0]["data"]["actorId"] == 42

    @pytest.mark.asyncio(loop_scope="session")
    async def test_transition_with_extra_updates(self, order_fsm: StateMachine):
        obj = FakeModel(status="paid")
        await order_fsm.transition(
            obj,
            to_state="shipped",
            extra_updates={"closed_at": "2026-08-08T10:00:00Z"},
        )

        assert obj.status == "shipped"
        assert obj.closed_at == "2026-08-08T10:00:00Z"
        assert set(obj._saved_fields) == {"status", "closed_at"}

    @pytest.mark.asyncio(loop_scope="session")
    async def test_transition_with_enum_current_state(self, order_fsm: StateMachine):
        obj = FakeModel(status=FakeStatus.pending)
        await order_fsm.transition(obj, to_state="paid")
        assert obj.status == "paid"

    @pytest.mark.asyncio(loop_scope="session")
    async def test_transition_with_custom_state_field(self, order_fsm: StateMachine):
        obj = FakeModel(status="closed", phase="pending")
        await order_fsm.transition(obj, to_state="paid", state_field="phase")

        assert obj.status == "closed"
        assert obj.phase == "paid"
        assert obj._saved_fields == ["phase"]

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_transition_raises_transition_error(self, order_fsm: StateMachine):
        obj = FakeModel(status="completed")
        logs: list[dict[str, object]] = []

        def log_fn(message: str, *, data: dict[str, object]) -> None:
            logs.append({"message": message, "data": data})

        with pytest.raises(TransitionError) as exc_info:
            await order_fsm.transition(obj, to_state="pending", log_fn=log_fn)

        assert exc_info.value.code == Code.STATE_TRANSITION_INVALID
        assert "completed" in str(exc_info.value)
        assert "pending" in str(exc_info.value)
        assert obj.status == "completed"
        assert obj._save_calls == 0
        assert logs == []

    @pytest.mark.asyncio(loop_scope="session")
    async def test_invalid_transition_uses_custom_error_code(self):
        fsm = StateMachine(transitions={"closed": []}, error_code="4999")

        with pytest.raises(TransitionError) as exc_info:
            await fsm.transition(FakeModel(status="closed"), to_state="pending")

        assert exc_info.value.code == "4999"


class TestTransitionErrorIsBizError:
    def test_transition_error_is_biz_error(self):
        """确保调用方可以用 BizError 统一捕获状态机异常。"""
        assert issubclass(TransitionError, BizError)
