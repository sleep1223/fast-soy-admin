from typing import Annotated
from pydantic import BaseModel, Field
from app.models.system import StatusType


class BaseApi(BaseModel):
    # path: Annotated[str | None, Field(title="请求路径", description="/api/v1/auth/login")]
    # method: Annotated[str | None, Field(title="请求方法", description="GET")]
    path: str | None = Field(default=None, title="请求路径", description="/api/v1/auth/login")
    method: str | None = Field(title="请求方法", description="GET")
    summary: Annotated[str | None, Field(title="API简介")] = None
    tags: Annotated[str | list[str] | None, Field(title="API标签")] = None
    status: Annotated[StatusType | None, Field()] = None

    class Config:
        allow_extra = True
        populate_by_name = True


class ApiSearch(BaseApi):
    current: Annotated[int | None, Field(title="页码")] = 1
    size: Annotated[int | None, Field(title="每页数量")] = 10


class ApiCreate(BaseApi):
    path: str = Field(default_factory=str, title="请求路径", description="/api/v1/auth/login")
    method: str = Field(default_factory=str, title="请求方法", description="GET")


class ApiUpdate(BaseApi):
    ...
