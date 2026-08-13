from typing import Any, Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.core.tools import to_camel_case
from app.core.types import SqidId

T = TypeVar("T")


class SchemaBase(BaseModel):
    """全局 Schema 基类：自动 snake_case → camelCase 别名"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        validate_by_name=True,
        validate_by_alias=True,
    )


class PageQueryBase(SchemaBase):
    """分页查询基类 — 所有 POST /resources/search 接口的 body 应继承它。

    ``order_by`` 允许前端指定排序字段，字段名前加 ``-`` 表示降序，
    如 ``["-created_at", "name"]``。为 ``None`` 时使用 CRUDRouter 的
    ``list_order`` 默认排序。
    """

    current: int = Field(1, ge=1, title="页码")
    size: int = Field(10, ge=1, le=1000, title="每页数量")
    order_by: list[str] | None = Field(None, title="排序字段列表")


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
        code: str | int = "2400",
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
        current: int | None = 1,
        size: int | None = 20,
        **kwargs,
    ):
        if isinstance(data, dict):
            data.update({"total": total, "current": current, "size": size})
        super().__init__(code=code, msg=msg, data=data, status_code=200, **kwargs)


class CommonIds(SchemaBase):
    ids: list[SqidId] = Field(min_length=1, title="通用ids")


class OfflineByRoleRequest(SchemaBase):
    role_codes: list[str] = Field(title="角色编码列表")


# ---- OpenAPI 响应模型 ----
# 用于 FastAPI 的 response_model 声明，让 Swagger UI 能展示真实的响应结构。
# 实际返回值仍然使用 Success / SuccessExtra（JSONResponse 子类），
# 这些模型仅用于文档生成。
#
# 用法::
#
#     @router.get("/users/{id}", response_model=ResponseModel[UserOut])
#     async def get_user(id: int):
#         ...
#         return Success(data=user_dict)
#
#     @router.post("/users/search", response_model=PageResponseModel[UserOut])
#     async def list_users(obj_in: UserSearch):
#         ...
#         return SuccessExtra(data={"records": records}, total=total, ...)


class ResponseModel(BaseModel, Generic[T]):
    """通用成功响应的 OpenAPI 文档模型"""

    code: str = Field("0000", title="响应码")
    msg: str = Field("OK", title="消息")
    data: T | None = Field(None, title="响应数据")


class PageData(BaseModel, Generic[T]):
    """分页数据结构"""

    records: list[T] = Field(default_factory=list, title="数据列表")
    total: int = Field(0, title="总数")
    current: int = Field(1, title="当前页码")
    size: int = Field(10, title="每页数量")


class PageResponseModel(BaseModel, Generic[T]):
    """分页响应的 OpenAPI 文档模型"""

    code: str = Field("0000", title="响应码")
    msg: str = Field("OK", title="消息")
    data: PageData[T] | None = Field(None, title="分页数据")


def make_optional(schema: type[BaseModel], name: str | None = None) -> type[BaseModel]:
    """基于已有 Schema 动态生成所有字段均为 Optional 的版本，用于 Update schema。

    用法::

        class CustomerCreate(SchemaBase):
            name: str
            email: str
            tenant_id: int

        CustomerUpdate = make_optional(CustomerCreate, "CustomerUpdate")

    生成的 CustomerUpdate 等价于::

        class CustomerUpdate(SchemaBase):
            name: str | None = None
            email: str | None = None
            tenant_id: int | None = None
    """
    optional_fields: dict[str, Any] = {}
    for field_name, field_info in schema.model_fields.items():
        optional_fields[field_name] = (field_info.annotation | None, Field(default=None, title=field_info.title, description=field_info.description))  # type: ignore[operator]

    model_name = name or f"{schema.__name__}Partial"
    bases = (schema,) if issubclass(schema, SchemaBase) else (SchemaBase,)
    return type(model_name, bases, {"__annotations__": {k: v[0] for k, v in optional_fields.items()}, **{k: v[1] for k, v in optional_fields.items()}})
