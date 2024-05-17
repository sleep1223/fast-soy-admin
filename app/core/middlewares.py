from datetime import datetime
from json import JSONDecodeError

import orjson
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from .bgtask import BgTasks
from app.models.system import User, Log, APILog
from app.models.system import LogType
from app.settings import APP_SETTINGS
from .ctx import CTX_USER_ID
from .dependency import check_token


class SimpleBaseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        await self.handle_http(scope, receive, send)

    async def handle_http(self, scope, receive, send) -> None:
        request = Request(scope, receive)
        response = await self.before_request(request) or self.app

        async def send_wrapper(_response):
            await self.after_request(request, _response)
            await send(_response)

        await response(scope, receive, send_wrapper)

    async def before_request(self, request: Request) -> ASGIApp | None:
        ...

    async def after_request(self, request: Request, response: dict):
        ...


class BackGroundTaskMiddleware(SimpleBaseMiddleware):
    async def before_request(self, request: Request) -> ASGIApp | None:
        await BgTasks.init_bg_tasks_obj()
        # return self.app

    async def after_request(self, request: Request, response: dict) -> None:
        await BgTasks.execute_tasks()


class APILoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.start_time = datetime.now()
        path = request.url.path

        if (
                all([declude not in path for declude in APP_SETTINGS.ADD_LOG_ORIGINS_DECLUDE])
                and (
                "*" in APP_SETTINGS.ADD_LOG_ORIGINS_INCLUDE
                or any([include in path for include in APP_SETTINGS.ADD_LOG_ORIGINS_INCLUDE]))
        ):
            if request.scope["type"] == "http":
                token = request.headers.get("Authorization")
                user_obj = None
                if token:
                    status, _, decode_data = check_token(token.replace("Bearer ", "", 1))
                    if status and decode_data:
                        user_id = int(decode_data["data"]["userId"])
                        user_obj = await User.filter(id=user_id).first()
                        if user_obj:
                            CTX_USER_ID.set(user_id)
                try:
                    request_data = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None
                except JSONDecodeError:
                    request_data = None

                api_log_data = {
                    "ip_address": request.client.host if request.client else "none",
                    "user_agent": request.headers.get("user-agent"),
                    "request_url": str(request.url),
                    "request_params": dict(request.query_params) or None,
                    "request_data": request_data
                }
                api_log_obj = await APILog.create(**api_log_data)
                request.state.api_log_id = api_log_obj.id
                await Log.create(log_type=LogType.ApiLog, by_user=user_obj, api_log=api_log_obj)

        response = await call_next(request)
        return response


class APILoggerAddResponseMiddleware(SimpleBaseMiddleware):
    """
    需要与APILoggerMiddleware搭配使用
    """

    async def after_request(self, request: Request, response: dict) -> None:
        if hasattr(request.state, "api_log_id") and response.get("type") == "http.response.body":
            response_body = response.get("body", b"")
            try:
                resp = orjson.loads(response_body)
                api_log_obj = await APILog.get(id=request.state.api_log_id)
                if api_log_obj:
                    api_log_obj.response_data = resp
                    api_log_obj.response_code = resp.get("code", "-1")
                    api_log_obj.process_time = (datetime.now() - request.state.start_time).total_seconds()
                    await api_log_obj.save()

            except orjson.JSONDecodeError:
                pass
