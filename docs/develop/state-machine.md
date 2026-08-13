# 状态机

轻量级状态机，负责三件事：

1. 校验 `from_state → to_state` 是否合法
2. 更新模型状态及同批附加字段
3. 调用日志函数记录审计信息

不引入独立的 `TransitionLog` 表——审计走 `radar_log` 即可。

源码：[`app/core/state_machine.py`](../../../app/core/state_machine.py)。

## 定义

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

`transitions` 是一张邻接表：`{当前状态: [合法的目标状态列表]}`。

非法流转默认抛出 `TransitionError(code=Code.STATE_TRANSITION_INVALID, ...)`。如果业务模块需要专属码，可通过构造器的关键字参数覆盖：

```python
ORDER_FSM = StateMachine(
    transitions={"pending": ["paid"], "paid": ["shipped"], "shipped": []},
    error_code=Code.ORDER_INVALID_TRANSITION,
)
```

`ORDER_INVALID_TRANSITION` 需要由业务模块按 [响应码约定](../reference/codes.md) 追加到 `app/core/code.py` 的自定义码段。

## 执行流转

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
    return Success(msg="状态更新成功", data=await product.to_dict())
```

`transition` 内部：

1. 读取 `getattr(obj, state_field)`，兼容 `Enum.value`
2. 校验 `allowed(from_state, to_state)`；失败时抛出配置错误码的 `TransitionError`
3. 调用 `obj.update_from_dict(...)` 和 `obj.save(update_fields=...)`
4. 调用 `log_fn("状态变更", data={...})`

非法流转在更新和日志调用之前失败，不会修改对象或写成功日志。

## 完整签名

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

`extra_updates` 用于与状态同时写入附加字段：

```python
await PRODUCT_FSM.transition(
    obj=product,
    to_state="archived",
    actor_id=get_current_user_id(),
    log_fn=radar_log,
    extra_updates={"archived_at": datetime.now(tz=timezone.utc)},
)
```

## 查询合法目标

```python
PRODUCT_FSM.allowed("draft", "active")       # → True
PRODUCT_FSM.allowed("draft", "archived")     # → False
PRODUCT_FSM.allowed_targets("draft")           # → ["active"]
```

前端可以据此动态展示下一步动作，但后端仍必须执行状态机校验。

## 异常处理

`TransitionError` 继承 `BizError`，全局异常处理器会统一转成 `Fail(code, msg)`。通常不需要在业务层捕获，让它直接穿透到全局处理器即可。

- 未配置专属码：返回 `Code.STATE_TRANSITION_INVALID`（`2407`）
- 配置 `error_code`：原样返回业务模块的专属码

## 与权限的关系

状态机只校验流转合法性，不判断操作人是否有权执行。鉴权应放在路由层：

```python
@router.post(
    "/products/{product_id}/transition",
    dependencies=[require_buttons("B_INVENTORY_PRODUCT_TRANSITION")],
)
async def transition_product(product_id: SqidPath, body: ProductTransition):
    return await product_service.transition(product_id, body.to_state)
```

## 测试

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

## 相关

- [事件总线](./events.md) — 状态变更后常用 `emit` 发布事件
- [并发控制](../ops/concurrency.md) — 状态机与乐观锁的职责边界
