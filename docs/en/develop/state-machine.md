# State Machine

The lightweight state machine has three responsibilities:

1. Validate `from_state → to_state`
2. Update the model state and any additional fields in the same save
3. Call a logger with audit data

It does not create a separate `TransitionLog` table; use `radar_log` for audit records.

Source: `app/core/state_machine.py`.

## Define

```python
from app.utils import StateMachine

PRODUCT_FSM = StateMachine(
    transitions={
        "draft": ["active"],
        "active": ["archived"],
        "archived": [],
    }
)
```

`transitions` is an adjacency list: `{current_state: [allowed_targets]}`.

Invalid transitions raise `TransitionError(code=Code.STATE_TRANSITION_INVALID, ...)` by default. A business module can opt into its own code through the keyword-only constructor argument:

```python
ORDER_FSM = StateMachine(
    transitions={"pending": ["paid"], "paid": ["shipped"], "shipped": []},
    error_code=Code.ORDER_INVALID_TRANSITION,
)
```

The business module must first add `ORDER_INVALID_TRANSITION` to the project-defined range in `app/core/code.py`; see [Response codes](/en/reference/codes).

## Transition

```python
from app.utils import Success, emit, get_current_user_id, radar_log

async def activate_product(product_id: int):
    product = await product_controller.get(id=product_id)
    await PRODUCT_FSM.transition(
        obj=product,
        to_state="active",
        state_field="status",
        actor_id=get_current_user_id(),
        log_fn=radar_log,
    )
    await emit("product.status_changed", product_id=product_id, to_state="active")
    return Success(msg="state updated", data=await product.to_dict())
```

Inside `transition`:

1. Read `getattr(obj, state_field)`, including `Enum.value`
2. Validate `allowed(from_state, to_state)` and raise `TransitionError` with the configured code on failure
3. Call `obj.update_from_dict(...)` and `obj.save(update_fields=...)`
4. Call `log_fn("state changed", data={...})`

An invalid transition fails before update or logging, so it does not mutate the object or emit a success audit record.

## Full signatures

```python
StateMachine(
    transitions: dict[str, list[str]],
    *,
    error_code: str = Code.STATE_TRANSITION_INVALID,
)

async def transition(
    self,
    obj: Any,
    to_state: str,
    state_field: str = "status",
    actor_id: int | None = None,
    log_fn: Callable[..., None] | None = None,
    extra_updates: dict[str, Any] | None = None,
) -> None
```

Use `extra_updates` to persist related fields with the state:

```python
await PRODUCT_FSM.transition(
    obj=product,
    to_state="archived",
    actor_id=get_current_user_id(),
    log_fn=radar_log,
    extra_updates={"archived_at": datetime.now(tz=timezone.utc)},
)
```

## Inspect allowed targets

```python
PRODUCT_FSM.allowed("draft", "active")       # → True
PRODUCT_FSM.allowed("draft", "archived")     # → False
PRODUCT_FSM.allowed_targets("draft")           # → ["active"]
```

The frontend can use this information to show the next action, but the backend must still enforce the transition.

## Error handling

`TransitionError` extends `BizError`, so the global handler converts it to `Fail(code, msg)`. Business services normally let it propagate.

- Without a module-specific code: `Code.STATE_TRANSITION_INVALID` (`2407`)
- With `error_code`: the configured module-specific code

## Permission relationship

The state machine validates transition legality; it does not authorize the actor. Authorize at the route layer:

```python
@router.post(
    "/products/{product_id}/transition",
    dependencies=[require_buttons("B_INVENTORY_PRODUCT_TRANSITION")],
)
async def transition_product(product_id: SqidPath, body: ProductTransition):
    return await product_service.transition(product_id, body.to_state)
```

## Tests

```python
async def test_draft_to_active_ok():
    product = await Product.create(status="draft", ...)
    await PRODUCT_FSM.transition(obj=product, to_state="active")
    assert product.status == "active"


async def test_draft_to_archived_blocked():
    product = await Product.create(status="draft", ...)
    with pytest.raises(TransitionError) as exc_info:
        await PRODUCT_FSM.transition(obj=product, to_state="archived")
    assert exc_info.value.code == Code.STATE_TRANSITION_INVALID
```

## See also

- [Event bus](/en/develop/events) — emit events after transitions
- [Concurrency control](/ops/concurrency) — state-machine and optimistic-lock responsibilities
