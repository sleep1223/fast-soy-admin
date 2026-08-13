"""
轻量级同进程事件总线 — 跨模块通信。

业务模块之间不允许反向导入（system → 不知道 business），
但有些场景需要跨模块联动（如商品创建后联动创建补货任务）。
通过事件总线实现：发送方只管 ``emit``，接收方通过 ``@on`` 注册处理器。

用法::

    # 注册事件处理器（通常在模块的 events.py 顶层）
    from app.core.events import on

    @on("product.created")
    async def _notify_on_create(product_id: int, **kwargs):
        radar_log("商品创建事件", data={"productId": product_id})

    # 触发事件（在服务层）
    from app.core.events import emit

    await emit("product.created", product_id=new_product.id)

注意：
    - 仅限进程内使用，不做跨进程/跨服务投递。
    - 处理器在 ``emit`` 中顺序执行（异步处理器 await），异常被捕获并 log，不中断后续处理器。
    - 处理器在模块导入时注册，因此包含 ``@on`` 的模块必须被导入（通常在 ``__init__.py`` 中 import）。
"""

from __future__ import annotations

import inspect
from collections import defaultdict
from typing import Any, Callable

from pydantic import ValidationError

from app.core.business import EventSpec

_handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)


def _event_name(event: str | EventSpec) -> str:
    return event.name if isinstance(event, EventSpec) else event


def on(event: str | EventSpec) -> Callable:
    """装饰器：将函数注册为指定事件的处理器。

    处理器签名应接受 ``**kwargs``，以便事件触发方自由传参::

        @on("product.created")
        async def handler(product_id: int, **kwargs): ...
    """

    name = _event_name(event)

    def decorator(fn: Callable) -> Callable:
        _handlers[name].append(fn)
        return fn

    return decorator


async def emit(event: str | EventSpec, **kwargs: Any) -> None:
    """触发事件，顺序执行所有已注册的处理器。

    处理器抛出的异常被捕获并通过 ``log.exception`` 输出，不中断其他处理器。
    """
    from app.core.log import log

    if isinstance(event, EventSpec):
        if event.delivery == "outbox":
            from app.core.outbox import enqueue_outbox_event

            await enqueue_outbox_event(event, kwargs)
            return
        if event.payload is not None:
            try:
                event.payload.model_validate(kwargs)
            except ValidationError:
                log.exception(f"Event payload validation failed: {event.name}")
                raise

    name = _event_name(event)
    await emit_local(name, **kwargs)


async def emit_local(event: str | EventSpec, **kwargs: Any) -> None:
    """Dispatch event handlers in the current process only."""

    from app.core.log import log

    name = _event_name(event)
    handlers = _handlers.get(name, [])
    for handler in handlers:
        try:
            if inspect.iscoroutinefunction(handler):
                await handler(**kwargs)
            else:
                handler(**kwargs)
        except Exception:
            log.exception(f"Event handler error: {name} / {handler.__qualname__}")
