from __future__ import annotations

import inspect
import json
import time

from app.core.log import log
from app.system.radar.ctx import CTX_RADAR
from app.system.radar.redaction import redact_text, redact_value


def _format_endpoint(host: str | None, port: int | str | None) -> str | None:
    """把 (host, port) 拼成 ``ip:port`` 形式；IPv6 用方括号包裹。port 缺失则只返回 host。"""
    if not host:
        return None
    if not port:
        return host
    if ":" in host and not host.startswith("["):
        return f"[{host}]:{port}"
    return f"{host}:{port}"


_LOG_DISPATCH = {
    "DEBUG": log.debug,
    "INFO": log.info,
    "WARNING": log.warning,
    "ERROR": log.error,
    "CRITICAL": log.critical,
}


def radar_log(message: str, *, level: str = "INFO", data: dict | None = None, log_to_file: bool = True) -> None:
    """向当前请求的 Radar 时间线插入一条手动日志，并可同时输出到文件日志。

    用法：
        from app.system.radar.developer import radar_log

        radar_log("订单开始处理", data={"order_id": 123})
        radar_log("支付失败", level="ERROR", data={"reason": "timeout"})
        radar_log("仅 radar 记录", log_to_file=False)
    """
    level = level.upper()
    radar_ctx = CTX_RADAR.get()
    safe_message = redact_text(message) or ""
    safe_data = redact_value(data) if data else None

    if log_to_file:
        log_func = _LOG_DISPATCH.get(level, log.info)
        endpoint = _format_endpoint(radar_ctx.client_ip, radar_ctx.client_port) if radar_ctx else None
        prefix = f"[{endpoint}] " if endpoint else ""
        if safe_data:
            log_func(f"{prefix}{safe_message} | {json.dumps(safe_data, ensure_ascii=False, default=str)}")
        else:
            log_func(f"{prefix}{safe_message}")

    if radar_ctx is None:
        return

    frame = inspect.currentframe()
    source = None
    if frame and frame.f_back:
        caller = frame.f_back
        module = caller.f_globals.get("__name__", "unknown")
        func_name = caller.f_code.co_name
        source = f"{module}.{func_name}:{caller.f_lineno}"

    radar_ctx.user_logs.append({
        "level": level,
        "message": safe_message,
        "data": json.dumps(safe_data, ensure_ascii=False, default=str) if safe_data else None,
        "source": source,
        "offset_ms": round((time.monotonic() - radar_ctx.start_mono) * 1000, 3),
    })
