import http

from fastapi.exceptions import (
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError


class SettingNotFound(Exception):
    pass


class HTTPException(Exception):
    def __init__(
            self,
            code: int | str,
            msg: str | None = None
    ) -> None:
        if msg is None:
            msg = http.HTTPStatus(int(code)).phrase
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return f"{self.code}: {self.msg}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(code={self.code!r}, msg={self.msg!r})"


def BaseHandle(exc: Exception, handle_exc, code: int | str, msg: str, status_code: int = 500) -> JSONResponse:
    print("test", JSONResponse(content=dict(code=str(code), msg=msg), status_code=status_code))
    if isinstance(exc, handle_exc):
        return JSONResponse(content=dict(code=str(code), msg=msg), status_code=status_code)
    else:
        return JSONResponse(content=dict(code=str(code), msg=f"Exception handler Error, exc: {exc}"), status_code=status_code)


async def DoesNotExistHandle(req: Request, exc: Exception) -> JSONResponse:
    return BaseHandle(exc, DoesNotExist, 404, f"Object has not found, exc: {exc}, path: {req.path_params}, query: {req.query_params}", 404)


async def IntegrityHandle(req: Request, exc: Exception) -> JSONResponse:
    return BaseHandle(exc, IntegrityError, 500, f"IntegrityError，{exc}, path: {req.path_params}, query: {req.query_params}", 500)


async def HttpExcHandle(_: Request, exc: HTTPException) -> JSONResponse:
    return BaseHandle(exc, HTTPException, exc.code, exc.msg, 200)


async def RequestValidationHandle(_: Request, exc: Exception) -> JSONResponse:
    return BaseHandle(exc, RequestValidationError, 422, f"RequestValidationError, {exc}")


async def ResponseValidationHandle(_: Request, exc: Exception) -> JSONResponse:
    return BaseHandle(exc, ResponseValidationError, 422, f"ResponseValidationError, {exc}")
