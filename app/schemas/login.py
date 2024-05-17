from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class CredentialsSchema(BaseModel):
    user_name: str = Field(alias="userName", description="用户名")
    password: str = Field(description="密码")

    class Config:
        populate_by_name = True


class JWTOut(BaseModel):
    access_token: Annotated[str | None, Field(alias="token", description="请求token")] = None
    refresh_token: Annotated[str | None, Field(alias="refreshToken", description="刷新token")] = None

    class Config:
        populate_by_name = True


class JWTPayload(BaseModel):
    data: dict
    iat: datetime
    exp: datetime

    # aud: str
    # iss: str
    # sub: str

    class Config:
        populate_by_name = True


__all__ = ["CredentialsSchema", "JWTOut", "JWTPayload"]
