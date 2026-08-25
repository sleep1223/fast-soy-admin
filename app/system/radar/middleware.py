from __future__ import annotations

import asyncio
import sys
import time
from uuid import uuid4

from loguru import logger
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.ctx import CTX_X_REQUEST_ID
from app.system.radar.config import RADAR_SETTINGS
from app.system.radar.ctx import CTX_RADAR, RadarRequestContext
from app.system.radar.db import flush_request_data
from app.system.radar.exceptions import format_exception_pretty
from app.system.radar.redaction import redact_headers, redact_path, redact_query_string, redact_text, redact_value

_AUTH_PATH_PREFIX = "/api/v1/auth"


def _serialize_headers(headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key_bytes, val_bytes in headers:
        key = key_bytes.decode("latin-1", errors="replace").lower()
        val = val_bytes.decode("latin-1", errors="replace")
        result[key] = val
    return redact_headers(result) or {}


def _truncate_body(body: str | None, max_size: int) -> str | None:
    if body is None:
        return None
    if len(body) <= max_size:
        return body
    return body[:max_size] + f"... [truncated {len(body) - max_size} chars]"


class RadarMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # 认证端点永不采集，且不能被环境变量中的 include 列表重新启用。
        if path == _AUTH_PATH_PREFIX or path.startswith(f"{_AUTH_PATH_PREFIX}/"):
            await self.app(scope, receive, send)
            return

        is_included = any(path.startswith(inc) for inc in RADAR_SETTINGS.RADAR_INCLUDE_PATHS)
        is_excluded = any(path.startswith(exc) for exc in RADAR_SETTINGS.RADAR_EXCLUDE_PATHS)

        if is_excluded and not is_included:
            # 被排除的路径完全跳过 Radar，不建上下文、不记录
            await self.app(scope, receive, send)
            return

        await self._handle_http(scope, receive, send, flush_only_if_logged=False)

    async def _handle_http(self, scope: Scope, receive: Receive, send: Send, *, flush_only_if_logged: bool = False) -> None:
        x_request_id = CTX_X_REQUEST_ID.get("")
        if not x_request_id:
            x_request_id = uuid4().hex

        # 获取客户端 IP 与端口（分字段存储，便于按端口排序 / 过滤）
        # ASGI 直连：scope["client"] = (host, port)（granian / uvicorn 都遵循）
        # 反代：X-Forwarded-For 取首个 IP；端口需反代显式发 X-Forwarded-Port
        proxied_host: str | None = None
        proxied_port_str: str | None = None
        for key_bytes, val_bytes in scope.get("headers", []):
            key = key_bytes.decode("latin-1", errors="replace").lower()
            val = val_bytes.decode("latin-1", errors="replace")
            if key == "x-forwarded-for" and proxied_host is None:
                proxied_host = val.split(",")[0].strip() or None
            elif key == "x-real-ip" and proxied_host is None:
                proxied_host = val.strip() or None
            elif key == "x-forwarded-port":
                proxied_port_str = val.strip() or None

        client_ip: str | None
        client_port: int | None
        if proxied_host:
            client_ip = proxied_host
            try:
                client_port = int(proxied_port_str) if proxied_port_str else None
            except ValueError:
                client_port = None
        else:
            client_info = scope.get("client")
            client_ip = client_info[0] if client_info else None
            client_port = client_info[1] if client_info else None

        radar_ctx = RadarRequestContext(
            x_request_id=x_request_id,
            start_mono=time.monotonic(),
            method=scope.get("method", ""),
            path=redact_path(scope.get("path", "")) or "",
            client_ip=client_ip,
            client_port=client_port,
            query_params=redact_query_string(scope.get("query_string", b"").decode("latin-1") or None),
            request_headers=_serialize_headers(scope.get("headers", [])),
        )

        # 缓冲请求体
        body_chunks: list[bytes] = []
        receive_complete = False

        async def buffered_receive() -> Message:
            nonlocal receive_complete
            message = await receive()
            if message.get("type") == "http.request":
                body_chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    receive_complete = True
            return message

        # 捕获响应
        response_headers_raw: list[tuple[bytes, bytes]] = []
        response_body_chunks: list[bytes] = []

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                radar_ctx.response_status = message.get("status")
                response_headers_raw.extend(message.get("headers", []))
            elif message["type"] == "http.response.body":
                response_body_chunks.append(message.get("body", b""))
            await send(message)

        token = CTX_RADAR.set(radar_ctx)
        try:
            await self.app(scope, buffered_receive, send_wrapper)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            radar_ctx.exception_info = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": redact_text(str(exc_value)),
                "traceback": redact_text(format_exception_pretty(exc_type, exc_value, exc_tb)),
            }
            raise
        finally:
            # 被排除的路径：仅在有 radar_log 日志时才落库
            should_flush = not flush_only_if_logged or bool(radar_ctx.user_logs)

            if should_flush:
                radar_ctx.path = redact_path(scope.get("path", ""), path_params=scope.get("path_params")) or ""
                if radar_ctx.exception_info:
                    radar_ctx.exception_info = redact_value(radar_ctx.exception_info)

                # 整理请求体
                if body_chunks:
                    raw_body = b"".join(body_chunks)
                    try:
                        radar_ctx.request_body = _truncate_body(redact_text(raw_body.decode("utf-8", errors="replace")), RADAR_SETTINGS.RADAR_MAX_BODY_SIZE)
                    except Exception:
                        radar_ctx.request_body = f"[binary {len(raw_body)} bytes]"

                # 整理响应数据
                if response_headers_raw:
                    radar_ctx.response_headers = _serialize_headers(response_headers_raw)

                if RADAR_SETTINGS.RADAR_CAPTURE_RESPONSE_BODY and response_body_chunks:
                    raw_resp = b"".join(response_body_chunks)
                    try:
                        radar_ctx.response_body = _truncate_body(redact_text(raw_resp.decode("utf-8", errors="replace")), RADAR_SETTINGS.RADAR_MAX_BODY_SIZE)
                    except Exception:
                        radar_ctx.response_body = f"[binary {len(raw_resp)} bytes]"

                # 异步写入 Radar 数据库
                asyncio.create_task(_safe_flush(radar_ctx))

            CTX_RADAR.reset(token)


async def _safe_flush(ctx: RadarRequestContext) -> None:
    try:
        await flush_request_data(ctx)
    except Exception as exc:
        # 不记录异常堆栈；Loguru diagnose=True 会把 ctx 局部变量写入文件。
        logger.error("Radar: failed to flush request data ({})", type(exc).__name__)
