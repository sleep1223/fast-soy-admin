from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.system import LogType
from fastapi import Query


class BaseLog(BaseModel):
    log_type: Annotated[LogType | None, Field(alias="logType", description="日志类型")] = None
    by_user: Annotated[str | None, Field(alias="logUser", description="操作人")] = None
    log_detail: Annotated[str | None, Field(alias="logDetail", description="日志详细")] = None
    create_time: Annotated[datetime | None, Field(alias="creationTime", description="创建时间")] = None

    class Config:
        populate_by_name = True


class BaseAPILog(BaseModel):
    ip_address: Annotated[str | None, Field(max_length=50, description="IP地址")] = None
    user_agent: Annotated[str | None, Field(max_length=255, description="User-Agent")] = None
    request_url: Annotated[str | None, Field(max_length=255, description="请求URL")] = None
    request_params: Annotated[dict | list | None, Field(description="请求参数")] = None
    request_data: Annotated[dict | list | None, Field(description="请求数据")] = None
    response_data: Annotated[dict | list | None, Field(description="响应数据")] = None
    response_status: Annotated[bool | None, Field(description="请求状态")] = None
    create_time: Annotated[datetime | None, Field(alias="creationTime", description="创建时间")] = None
    process_time: Annotated[float | None, Field(description="请求处理时间")] = None

    class Config:
        allow_extra = True
        populate_by_name = True


class LogSearch(BaseModel):
    current: Annotated[int | None, Field(description="页码")] = 1
    size: Annotated[int | None, Field(description="每页数量")] = 10
    log_type: Annotated[LogType | None, Field(alias="logType", description="日志类型")] = LogType.ApiLog
    log_user: Annotated[str | None, Field(alias="logUser", description="操作人员, 用户名")] = None
    log_detail: Annotated[str | None, Field(alias="logDetail", description="日志详细")] = None
    request_url: Annotated[str | None, Field(alias="requestUrl", description="请求URL")] = None
    # request_data: Annotated[str | None, Field(alias="requestData", description="请求数据")] = None
    # response_data: Annotated[str | None, Field(alias="responseData", description="响应数据")] = None
    time_range: Annotated[str | None, Field(alias="timeRange", description="时间范围, 逗号隔开")] = None
    response_code: Annotated[str | None, Field(alias="responseCode", description="响应业务码")] = None


class LogCreate(BaseLog):
    ...


class LogUpdate(BaseLog):
    ...


__all__ = ["BaseLog", "BaseAPILog", "LogSearch", "LogCreate", "LogUpdate"]
