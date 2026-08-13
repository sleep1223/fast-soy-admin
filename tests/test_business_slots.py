from collections import defaultdict

import pytest
from pydantic import BaseModel
from tortoise.expressions import Q

import app.core.events as event_bus
import app.core.policy as policy_registry
from app.core.business import DataPolicy, EventSpec, PolicyContext
from app.core.code import Code
from app.core.ctx import CTX_BUTTON_CODES, CTX_ROLE_CODES, CTX_USER_ID
from app.core.events import emit, on
from app.core.outbox import dispatch_outbox_once, make_outbox_dispatch_task
from app.core.policy import apply_data_policy, assert_object_policy
from app.core.state_machine import StateMachine, TransitionError
from app.core.tasks import BusinessTaskRunner


class DemoPayload(BaseModel):
    item_id: int


class _TerminalModel:
    status = "closed"
    pk = 1

    def update_from_dict(self, _data: dict[str, object]) -> "_TerminalModel":
        raise AssertionError("invalid transitions must not update the object")

    async def save(self, *, update_fields: list[str] | None = None) -> None:
        raise AssertionError("invalid transitions must not save the object")


@pytest.mark.asyncio(loop_scope="session")
async def test_typed_event_validates_payload(monkeypatch):
    monkeypatch.setattr(event_bus, "_handlers", defaultdict(list))
    received = []
    event = EventSpec(name="demo.created", payload=DemoPayload)

    @on(event)
    async def _handler(item_id: int):
        received.append(item_id)

    await emit(event, item_id=7)

    assert received == [7]
    with pytest.raises(Exception):
        await emit(event, item_id="bad")


@pytest.mark.asyncio(loop_scope="session")
async def test_apply_data_policy_uses_policy_context(monkeypatch):
    monkeypatch.setattr(policy_registry, "_data_policies", {})
    seen: list[PolicyContext] = []

    async def _filter(ctx: PolicyContext) -> Q:
        seen.append(ctx)
        return Q(owner_id=ctx.user_id)

    policy_registry.register_data_policy(DataPolicy(name="demo.item.read", build_filter=_filter))
    tokens = [
        CTX_USER_ID.set(42),
        CTX_ROLE_CODES.set(["R_USER"]),
        CTX_BUTTON_CODES.set(["B_DEMO_READ"]),
    ]
    try:
        result = await apply_data_policy("demo.item.read", module="demo")
    finally:
        CTX_BUTTON_CODES.reset(tokens[2])
        CTX_ROLE_CODES.reset(tokens[1])
        CTX_USER_ID.reset(tokens[0])

    assert isinstance(result, Q)
    assert seen[0].user_id == 42
    assert seen[0].role_codes == ["R_USER"]
    assert seen[0].button_codes == ["B_DEMO_READ"]
    assert seen[0].module == "demo"


@pytest.mark.asyncio(loop_scope="session")
async def test_object_policy_checker_denies_with_biz_error(monkeypatch):
    monkeypatch.setattr(policy_registry, "_data_policies", {})

    async def _checker(ctx: PolicyContext, obj) -> bool:
        return obj["owner_id"] == ctx.user_id

    policy_registry.register_data_policy(DataPolicy(name="demo.item.update", action="update", check_object=_checker))
    token = CTX_USER_ID.set(42)
    try:
        await assert_object_policy("demo.item.update", {"owner_id": 42})
        with pytest.raises(Exception):
            await assert_object_policy("demo.item.update", {"owner_id": 7})
    finally:
        CTX_USER_ID.reset(token)


@pytest.mark.asyncio(loop_scope="session")
async def test_state_machine_invalid_transition_uses_generic_code_without_side_effects():
    fsm = StateMachine({"closed": []})
    logs: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def log_fn(*args: object, **kwargs: object) -> None:
        logs.append((args, kwargs))

    with pytest.raises(TransitionError) as exc_info:
        await fsm.transition(_TerminalModel(), to_state="open", log_fn=log_fn)

    assert exc_info.value.code == Code.STATE_TRANSITION_INVALID
    assert logs == []


@pytest.mark.asyncio(loop_scope="session")
async def test_state_machine_accepts_custom_error_code():
    fsm = StateMachine({"closed": []}, error_code="4999")

    with pytest.raises(TransitionError) as exc_info:
        await fsm.transition(_TerminalModel(), to_state="open")

    assert exc_info.value.code == "4999"


@pytest.mark.asyncio(loop_scope="session")
async def test_outbox_event_dispatches_registered_handler(app, monkeypatch):
    from app.system.models import EventOutbox

    assert app is not None
    monkeypatch.setattr(event_bus, "_handlers", defaultdict(list))
    received = []
    event = EventSpec(name="demo.outbox_created", payload=DemoPayload, delivery="outbox")

    @on("demo.outbox_created")
    async def _handler(item_id: int):
        received.append(item_id)

    await emit(event, item_id=11)

    row = await EventOutbox.get(event_name="demo.outbox_created")
    assert row.status == "pending"
    assert row.payload == {"item_id": 11}

    dispatched = await dispatch_outbox_once()

    assert dispatched == 1
    assert received == [11]
    row = await EventOutbox.get(id=row.id)
    assert row.status == "sent"


@pytest.mark.asyncio(loop_scope="session")
async def test_business_task_runner_runs_task_once():
    calls = []

    async def _task():
        calls.append("ran")

    from app.core.business import PeriodicTask

    runner = BusinessTaskRunner([PeriodicTask(name="demo.task", handler=_task, interval_seconds=60)])
    await runner._run_once(runner.tasks[0])

    assert calls == ["ran"]


@pytest.mark.asyncio(loop_scope="session")
async def test_outbox_dispatch_task_factory(monkeypatch):
    calls = []

    async def _dispatch_once(**kwargs):
        calls.append(kwargs)
        return 1

    monkeypatch.setattr("app.core.outbox.dispatch_outbox_once", _dispatch_once)

    task = make_outbox_dispatch_task(interval_seconds=15, limit=3, max_attempts=2)
    runner = BusinessTaskRunner([task])

    await runner._run_once(task)

    assert task.name == "system.outbox.dispatch"
    assert task.interval_seconds == 15
    assert task.leader_only is True
    assert calls == [{"limit": 3, "max_attempts": 2}]
