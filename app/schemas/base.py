from typing import Any

from fastapi.responses import JSONResponse


class Custom(JSONResponse):
    def __init__(
        self,
        code: str | int = "0000",
        status_code: int = 200,
        msg: str = "OK",
        data: Any = None,
        **kwargs,
    ):
        content = {"code": str(code), "msg": msg, "data": data}
        content.update(kwargs)
        super().__init__(content=content, status_code=status_code)


class Success(Custom):
    pass


class Fail(Custom):
    def __init__(
        self,
        code: str | int = "4000",
        msg: str = "OK",
        data: Any = None,
        **kwargs,
    ):
        super().__init__(code=code, msg=msg, data=data, status_code=200, **kwargs)


class SuccessExtra(Custom):
    def __init__(
        self,
        code: str | int = "0000",
        msg: str = "OK",
        data: Any = None,
        total: int = 0,
        current: int = 1,
        size: int = 20,
        **kwargs,
    ):
        # kwargs.update({"total": total, "current": current, "size": size})
        if isinstance(data, dict):
            data.update({"total": total, "current": current, "size": size})
        super().__init__(code=code, msg=msg, data=data, status_code=200, **kwargs)
