from __future__ import annotations

import asyncio
import json
from functools import partial

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.config import APP_SETTINGS
from app.core.dependency import DependPermission, require_roles
from app.system.radar import db
from app.system.radar.config import RADAR_SETTINGS
from app.system.services.monitor import collector


class ResolveBody(BaseModel):
    resolved: bool


router = APIRouter(prefix="/__radar/api", tags=["Radar"], dependencies=[DependPermission, require_roles("R_ADMIN")])


@router.get("/requests", summary="请求列表")
async def list_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    path_filter: str | None = None,
    code_filter: str | None = None,
    min_duration: float | None = None,
    has_error: bool | None = None,
):
    total, rows = await db.query_requests(
        page=page,
        page_size=page_size,
        path_filter=path_filter,
        code_filter=code_filter,
        min_duration=min_duration,
        has_error=has_error,
    )
    return {"code": "0000", "msg": "OK", "data": {"total": total, "current": page, "size": page_size, "records": rows}}


@router.get("/requests/{x_request_id}", summary="请求详情")
async def get_request_detail(x_request_id: str):
    detail = await db.query_request_detail(x_request_id)
    if not detail:
        return {"code": "4004", "msg": "Request not found", "data": None}

    # 将 JSON 字符串还原为字典以便展示（to_dict 输出的键为 camelCase）
    for field in ("requestHeaders", "responseHeaders"):
        if detail.get(field) and isinstance(detail[field], str):
            try:
                detail[field] = json.loads(detail[field])
            except (json.JSONDecodeError, TypeError):
                pass

    return {"code": "0000", "msg": "OK", "data": detail}


@router.get("/queries", summary="SQL查询列表")
async def list_queries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    slow_only: bool = False,
    threshold_ms: float | None = None,
):
    total, rows = await db.query_all_queries(
        page=page,
        page_size=page_size,
        slow_only=slow_only,
        threshold_ms=threshold_ms or RADAR_SETTINGS.RADAR_SLOW_QUERY_THRESHOLD_MS,
    )
    return {"code": "0000", "msg": "OK", "data": {"total": total, "current": page, "size": page_size, "records": rows}}


@router.get("/exceptions", summary="异常列表")
async def list_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    path_filter: str | None = None,
    error_type: str | None = None,
    resolved: bool | None = None,
):
    total, rows = await db.query_exceptions(
        page=page,
        page_size=page_size,
        path_filter=path_filter,
        error_type=error_type,
        resolved=resolved,
    )
    return {"code": "0000", "msg": "OK", "data": {"total": total, "current": page, "size": page_size, "records": rows}}


@router.put("/exceptions/{x_request_id}/resolve", summary="切换异常处理状态")
async def resolve_exception(x_request_id: str, body: ResolveBody):
    success = await db.update_exception_resolved(x_request_id, body.resolved)
    if not success:
        return {"code": "4004", "msg": "Exception not found", "data": None}
    return {"code": "0000", "msg": "OK", "data": None}


@router.get("/stats", summary="统计概览")
async def get_stats(hours: int | None = Query(default=None, ge=1, le=720)):
    stats = await db.query_stats(hours=hours)
    return {"code": "0000", "msg": "OK", "data": stats}


@router.get("/dashboard", summary="仪表盘统计")
async def get_dashboard_stats(hours: int = Query(default=1, ge=1, le=720)):
    stats = await db.query_dashboard_stats(hours=hours)
    return {"code": "0000", "msg": "OK", "data": stats}


@router.delete("/purge", summary="清理过期数据")
async def purge_data(retention_hours: int = Query(default=RADAR_SETTINGS.RADAR_RETENTION_HOURS, ge=1)):
    deleted = await db.purge_old_data(retention_hours=retention_hours)
    return {"code": "0000", "msg": "OK", "data": {"deleted_count": deleted}}


# ===================== 系统监控 =====================


@router.get("/monitor/overview", summary="系统监控概览")
async def get_monitor_overview():
    data = await asyncio.to_thread(partial(collector.get_overview))
    return {"code": "0000", "msg": "OK", "data": data}


@router.get("/monitor/realtime", summary="实时监控数据")
async def get_monitor_realtime():
    data = await asyncio.to_thread(partial(collector.get_realtime))
    return {"code": "0000", "msg": "OK", "data": data}


@router.get("/_boom", summary="[dev] 触发未捕获异常以验证 Radar 异常捕获", include_in_schema=False)
async def boom(kind: str = Query(default="runtime", pattern="^(runtime|zero|key|attr)$")):
    if not APP_SETTINGS.APP_DEBUG:
        return {"code": "2200", "msg": "boom only available when APP_DEBUG=true", "data": None}
    if kind == "zero":
        _ = 1 / 0
    elif kind == "key":
        _ = {}["missing"]
    elif kind == "attr":
        _ = None.foo  # type: ignore[attr-defined]
    raise RuntimeError("radar smoke test")
