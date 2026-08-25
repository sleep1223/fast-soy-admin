from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from typing import cast

from loguru import logger
from tortoise.expressions import Q
from tortoise.functions import Avg

from app.system.radar.config import RADAR_SETTINGS
from app.system.radar.ctx import RadarRequestContext
from app.system.radar.models import RadarQuery, RadarRequest, RadarUserLog
from app.system.radar.query_capture import CTX_RADAR_WRITING
from app.system.radar.redaction import REDACTED, redact_headers, redact_path, redact_query_string, redact_sql, redact_text, redact_value

_REQUEST_LIST_EXCLUDED_FIELDS = ["request_headers", "request_body", "response_headers", "response_body", "error_traceback"]
_SQL_PARAM_SUMMARY_RE = re.compile(r"^\[(?:\d+ parameters redacted|\d+ rows)\]$")


def _redact_sql_params(params: object | None) -> str | None:
    if params is None:
        return None
    if isinstance(params, str) and _SQL_PARAM_SUMMARY_RE.fullmatch(params):
        return params
    return REDACTED


def _redact_record(record: dict) -> dict:
    result = cast("dict", redact_value(record))
    for key in ("path", "requestPath"):
        if isinstance(result.get(key), str):
            result[key] = redact_path(result[key])
    for key in ("sql", "sqlText"):
        if isinstance(result.get(key), str):
            result[key] = redact_sql(result[key])
    return result


async def flush_request_data(ctx: RadarRequestContext) -> None:
    token = CTX_RADAR_WRITING.set(True)
    try:
        duration_ms = round((time.monotonic() - ctx.start_mono) * 1000, 3)
        exception_info = redact_value(ctx.exception_info) if ctx.exception_info else None

        req_obj = await RadarRequest.create(
            x_request_id=ctx.x_request_id,
            method=ctx.method,
            path=redact_path(ctx.path) or "",
            client_ip=ctx.client_ip,
            client_port=ctx.client_port,
            user_id=ctx.user_id,
            user_name=ctx.user_name,
            query_params=redact_query_string(ctx.query_params),
            request_headers=redact_headers(ctx.request_headers),
            request_body=redact_text(ctx.request_body),
            response_status=ctx.response_status,
            response_headers=redact_headers(ctx.response_headers),
            response_body=redact_text(ctx.response_body),
            duration_ms=duration_ms,
            error_type=exception_info.get("type") if exception_info else None,
            error_message=exception_info.get("message") if exception_info else None,
            error_traceback=exception_info.get("traceback") if exception_info else None,
        )

        if ctx.queries:
            await RadarQuery.bulk_create([
                RadarQuery(
                    request=req_obj,
                    sql_text=redact_sql(q["sql"]),
                    params=_redact_sql_params(q.get("params")),
                    operation=q.get("operation"),
                    duration_ms=q["duration_ms"],
                    connection_name=q.get("connection_name"),
                    start_offset_ms=q.get("start_offset_ms"),
                )
                for q in ctx.queries
            ])

        if ctx.user_logs:
            await RadarUserLog.bulk_create([
                RadarUserLog(
                    request=req_obj,
                    level=ul["level"],
                    message=redact_text(ul["message"]),
                    data=redact_text(ul.get("data")),
                    source=ul.get("source"),
                    offset_ms=ul.get("offset_ms"),
                )
                for ul in ctx.user_logs
            ])
    except Exception as exc:
        # Loguru diagnose=True 会展开局部变量；这里只记录类型，避免 ctx 中的数据回流到文件日志。
        logger.error("Failed to flush radar data ({})", type(exc).__name__)
    finally:
        CTX_RADAR_WRITING.reset(token)


async def purge_old_data(retention_hours: int = 24) -> int:
    token = CTX_RADAR_WRITING.set(True)
    try:
        cutoff = datetime.now() - timedelta(hours=retention_hours)
        deleted = await RadarRequest.filter(created_at__lt=cutoff).delete()
        return deleted
    finally:
        CTX_RADAR_WRITING.reset(token)


async def query_requests(
    page: int = 1,
    page_size: int = 20,
    path_filter: str | None = None,
    code_filter: str | None = None,
    min_duration: float | None = None,
    has_error: bool | None = None,
) -> tuple[int, list[dict]]:
    q = Q()
    if path_filter:
        q &= Q(path__contains=path_filter)
    if code_filter is not None:
        q &= Q(response_body__contains=f'"code":"{code_filter}"') | Q(response_body__contains=f'"code": "{code_filter}"')
    if min_duration is not None:
        q &= Q(duration_ms__gte=min_duration)
    if has_error is True:
        q &= Q(error_type__not_isnull=True)
    elif has_error is False:
        q &= Q(error_type__isnull=True)

    total = await RadarRequest.filter(q).count()
    offset = (page - 1) * page_size
    objs = await RadarRequest.filter(q).order_by("-id").offset(offset).limit(page_size)
    records = []
    for obj in objs:
        d = await obj.to_dict(exclude_fields=_REQUEST_LIST_EXCLUDED_FIELDS)
        biz_code, biz_msg = _extract_business_code_and_msg(obj.response_body)
        d["businessCode"] = biz_code
        d["businessMsg"] = biz_msg
        records.append(_redact_record(d))
    return total, records


async def query_request_detail(x_request_id: str) -> dict | None:
    req = await RadarRequest.filter(x_request_id=x_request_id).first()
    if not req:
        return None

    result = _redact_record(await req.to_dict())
    biz_code, biz_msg = _extract_business_code_and_msg(req.response_body)
    result["businessCode"] = biz_code
    result["businessMsg"] = redact_text(biz_msg)

    query_objs = await RadarQuery.filter(request=req).order_by("start_offset_ms")
    result["queries"] = []
    for query in query_objs:
        query_data = _redact_record(await query.to_dict())
        query_data["params"] = _redact_sql_params(query.params)
        result["queries"].append(query_data)

    log_objs = await RadarUserLog.filter(request=req).order_by("offset_ms")
    result["user_logs"] = [_redact_record(await user_log.to_dict()) for user_log in log_objs]

    return result


async def query_all_queries(
    page: int = 1,
    page_size: int = 20,
    slow_only: bool = False,
    threshold_ms: float = 100.0,
) -> tuple[int, list[dict]]:
    q = Q()
    if slow_only:
        q &= Q(duration_ms__gte=threshold_ms)

    total = await RadarQuery.filter(q).count()
    offset = (page - 1) * page_size
    objs = await RadarQuery.filter(q).order_by("-duration_ms").offset(offset).limit(page_size).select_related("request")
    records = []
    for obj in objs:
        d = _redact_record(await obj.to_dict())
        d["params"] = _redact_sql_params(obj.params)
        d["xRequestId"] = obj.request.x_request_id if obj.request else None
        d["requestPath"] = redact_path(obj.request.path) if obj.request else None
        d["requestMethod"] = obj.request.method if obj.request else None
        records.append(d)
    return total, records


async def query_exceptions(
    page: int = 1,
    page_size: int = 20,
    path_filter: str | None = None,
    error_type: str | None = None,
    resolved: bool | None = None,
) -> tuple[int, list[dict]]:
    q = Q(error_type__not_isnull=True)
    if path_filter:
        q &= Q(path__contains=path_filter)
    if error_type:
        q &= Q(error_type__contains=error_type)
    if resolved is not None:
        q &= Q(resolved=resolved)
    total = await RadarRequest.filter(q).count()
    offset = (page - 1) * page_size
    objs = await RadarRequest.filter(q).order_by("-id").offset(offset).limit(page_size)
    records = []
    for obj in objs:
        records.append(_redact_record(await obj.to_dict(include_fields=["x_request_id", "method", "path", "error_type", "error_message", "error_traceback", "duration_ms", "resolved", "created_at"])))
    return total, records


async def update_exception_resolved(x_request_id: str, resolved: bool) -> bool:
    updated = await RadarRequest.filter(x_request_id=x_request_id, error_type__not_isnull=True).update(resolved=resolved)
    return updated > 0


async def query_stats(hours: int | None = None) -> dict:
    base_q = Q()
    query_base_q = Q()
    if hours is not None:
        cutoff = datetime.now() - timedelta(hours=hours)
        base_q &= Q(created_at__gte=cutoff)
        query_base_q &= Q(created_at__gte=cutoff)

    req_count = await RadarRequest.filter(base_q).count()
    avg_row = await RadarRequest.filter(base_q).annotate(avg_dur=Avg("duration_ms")).first().values("avg_dur")
    avg_duration: float = avg_row["avg_dur"] if avg_row and avg_row.get("avg_dur") is not None else 0
    error_count = await RadarRequest.filter(base_q & Q(error_type__not_isnull=True)).count()
    query_count = await RadarQuery.filter(query_base_q).count()
    slow_query_count = await RadarQuery.filter(query_base_q & Q(duration_ms__gte=RADAR_SETTINGS.RADAR_SLOW_QUERY_THRESHOLD_MS)).count()
    user_log_count = await RadarUserLog.filter(query_base_q).count()

    return {
        "request_count": req_count,
        "avg_duration_ms": round(avg_duration, 3) if avg_duration else 0,
        "error_count": error_count,
        "error_rate": round(error_count / req_count * 100, 2) if req_count else 0,
        "query_count": query_count,
        "slow_query_count": slow_query_count,
        "user_log_count": user_log_count,
    }


async def query_dashboard_stats(hours: int = 1) -> dict:
    """增强版仪表盘统计，包含百分位数、趋势及分布数据。"""
    cutoff = datetime.now() - timedelta(hours=hours)
    base_q = Q(created_at__gte=cutoff)

    # 基础计数
    req_count = await RadarRequest.filter(base_q).count()
    avg_row = await RadarRequest.filter(base_q).annotate(avg_dur=Avg("duration_ms")).first().values("avg_dur")
    avg_duration: float = avg_row["avg_dur"] if avg_row and avg_row.get("avg_dur") is not None else 0
    error_count = await RadarRequest.filter(base_q & Q(error_type__not_isnull=True)).count()
    query_count = await RadarQuery.filter(base_q).count()
    exception_count = await RadarRequest.filter(base_q & Q(response_status__gte=500)).count()

    # 成功 / 失败拆分
    success_count = await RadarRequest.filter(base_q & Q(response_status__lt=400)).count()
    error_rate = round(error_count / req_count * 100, 2) if req_count else 0
    success_rate = round(success_count / req_count * 100, 2) if req_count else 100

    # 响应时间百分位数（P50、P95、P99）
    raw_durations = cast(
        "list[float | None]",
        await RadarRequest.filter(base_q & Q(duration_ms__not_isnull=True)).order_by("duration_ms").values_list("duration_ms", flat=True),
    )
    durations: list[float] = [float(d) for d in raw_durations if d is not None]
    p50 = _percentile(durations, 50)
    p95 = _percentile(durations, 95)
    p99 = _percentile(durations, 99)

    # SQL 查询性能（平均耗时）
    q_avg_row = await RadarQuery.filter(base_q).annotate(avg_dur=Avg("duration_ms")).first().values("avg_dur")
    avg_query_time: float = q_avg_row["avg_dur"] if q_avg_row and q_avg_row.get("avg_dur") is not None else 0

    # 响应时间趋势（按时间桶分组）
    trend = await _build_time_trend(cutoff, hours)

    # SQL 查询活动趋势
    query_activity = await _build_query_activity(cutoff, hours)

    # 业务码分布——解析响应体 JSON 中的 "code" 字段
    code_distribution = await _build_code_distribution(base_q)

    return {
        # 顶部卡片
        "total_requests": req_count,
        "avg_response_time": round(avg_duration, 2) if avg_duration else 0,
        "total_queries": query_count,
        "total_exceptions": exception_count,
        # 性能概览
        "success_rate": success_rate,
        "error_rate": error_rate,
        "rps": round(req_count / (hours * 3600), 2) if req_count else 0,
        # 响应时间百分位数
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "avg_query_time": round(avg_query_time, 2) if avg_query_time else 0,
        # 业务码分布
        "distribution": code_distribution,
        # 趋势数据
        "response_time_trend": trend,
        "query_activity": query_activity,
    }


def _extract_business_code_and_msg(response_body: str | None) -> tuple[str | None, str | None]:
    """从响应体 JSON 中提取业务码和消息。"""
    if not response_body:
        return None, None
    try:
        parsed = json.loads(response_body)
        code = parsed.get("code")
        msg = parsed.get("msg")
        return (str(code) if code is not None else None), (str(msg) if msg is not None else None)
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


async def _build_code_distribution(base_q: Q) -> list[dict]:
    """从响应体 JSON 构建业务码分布统计。"""
    rows = cast(
        "list[str | None]",
        await RadarRequest.filter(base_q & Q(response_body__not_isnull=True)).values_list("response_body", flat=True),
    )
    counter: dict[str, int] = {}
    no_code_count = 0
    for body in rows:
        if not body:
            no_code_count += 1
            continue
        try:
            parsed = json.loads(body)
            code = str(parsed.get("code", ""))
            if code:
                counter[code] = counter.get(code, 0) + 1
            else:
                no_code_count += 1
        except (json.JSONDecodeError, AttributeError):
            no_code_count += 1

    result = [{"code": code, "count": count} for code, count in sorted(counter.items(), key=lambda x: -x[1])]
    if no_code_count:
        result.append({"code": "unknown", "count": no_code_count})
    return result


def _percentile(sorted_values: list[float], pct: int) -> float:
    if not sorted_values:
        return 0
    k = (len(sorted_values) - 1) * pct / 100
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return round(sorted_values[f], 2)
    return round(sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f]), 2)


async def _build_time_trend(cutoff: datetime, hours: int) -> list[dict]:
    """按时间桶构建响应时间趋势数据。"""
    if hours <= 1:
        bucket_minutes = 5
    elif hours <= 6:
        bucket_minutes = 15
    elif hours <= 24:
        bucket_minutes = 60
    else:
        bucket_minutes = 180

    buckets: list[dict] = []
    now = datetime.now()
    current = cutoff
    while current < now:
        bucket_end = min(current + timedelta(minutes=bucket_minutes), now)
        q = Q(created_at__gte=current, created_at__lt=bucket_end, duration_ms__not_isnull=True)
        row = await RadarRequest.filter(q).annotate(avg_dur=Avg("duration_ms")).first().values("avg_dur")
        count = await RadarRequest.filter(Q(created_at__gte=current, created_at__lt=bucket_end)).count()
        avg_val = row["avg_dur"] if row and row.get("avg_dur") is not None else 0
        buckets.append({
            "time": current.strftime("%H:%M"),
            "avg_response_time": round(avg_val, 2),
            "request_count": count,
        })
        current = bucket_end

    return buckets


async def _build_query_activity(cutoff: datetime, hours: int) -> list[dict]:
    """按时间桶构建 SQL 查询活动趋势数据。"""
    if hours <= 1:
        bucket_minutes = 5
    elif hours <= 6:
        bucket_minutes = 15
    elif hours <= 24:
        bucket_minutes = 60
    else:
        bucket_minutes = 180

    buckets: list[dict] = []
    now = datetime.now()
    current = cutoff
    while current < now:
        bucket_end = min(current + timedelta(minutes=bucket_minutes), now)
        q = Q(created_at__gte=current, created_at__lt=bucket_end)
        count = await RadarQuery.filter(q).count()
        row = await RadarQuery.filter(q).annotate(avg_dur=Avg("duration_ms")).first().values("avg_dur")
        avg_val = row["avg_dur"] if row and row.get("avg_dur") is not None else 0
        buckets.append({
            "time": current.strftime("%H:%M"),
            "query_count": count,
            "avg_duration": round(avg_val, 2),
        })
        current = bucket_end

    return buckets
