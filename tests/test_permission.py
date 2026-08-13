"""覆盖 PermissionControl.has_permission 对 FastAPI 全量路由的精确匹配行为。

核心安全属性：权限检测必须以 FastAPI 已匹配到的 APIRoute.path_format 为键，
而不是对 request.url.path 做正则前缀匹配——否则拥有 `/resources/{id}` 权限的
用户会绕过 `/resources/sync` 的权限（旧实现存在该缺陷）。
"""

import json

import pytest
import pytest_asyncio
from fastapi import Request
from fastapi.routing import APIRoute

from app.core.code import Code
from app.core.ctx import CTX_BUTTON_CODES, CTX_ROLE_CODES, CTX_USER, CTX_USER_ID
from app.core.dependency import PermissionControl
from app.core.exceptions import BizError
from app.system.models import StatusType

TEST_ROLE = "R_PERM_TEST"


def _all_routes(app):
    """枚举所有 APIRoute 的 (method, path_format)，跳过 HEAD/OPTIONS。"""
    seen: set[tuple[str, str]] = set()
    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue
        for m in r.methods:
            m_lower = m.lower()
            if m_lower in {"head", "options"}:
                continue
            key = (m_lower, r.path_format)
            if key in seen:
                continue
            seen.add(key)
            yield m_lower, r.path_format, r


def _build_request(app, route: APIRoute, method: str) -> Request:
    """构造最小化 Request，scope 中写入匹配到的 route，模拟 FastAPI 路由匹配完成后状态。"""
    scope = {
        "type": "http",
        "method": method.upper(),
        # path_format 里的 {xxx} 段用占位符替换，保证 request.url.path 是一个合法 URL
        "path": route.path_format.replace("{", ":").replace("}", ""),
        "raw_path": route.path_format.encode(),
        "query_string": b"",
        "headers": [],
        "route": route,
        "app": app,
    }
    return Request(scope)


async def _set_role_apis(redis, role_code: str, apis: list[tuple[str, str]]) -> None:
    """把 (method, path) 列表写入 role:{code}:apis 缓存（全部 enable 状态）。"""
    payload = [{"method": m, "path": p, "status": StatusType.enable.value} for m, p in apis]
    await redis.set(f"role:{role_code}:apis", json.dumps(payload))


def _bind_ctx(role_codes: list[str]) -> list:
    """设置 ContextVars，返回 reset token 列表供 teardown。"""
    tokens = [
        CTX_USER_ID.set(10_000),
        CTX_USER.set(None),  # type: ignore[arg-type]
        CTX_BUTTON_CODES.set([]),
        CTX_ROLE_CODES.set(role_codes),
    ]
    return tokens


def _reset_ctx(tokens: list) -> None:
    CTX_ROLE_CODES.reset(tokens[3])
    CTX_BUTTON_CODES.reset(tokens[2])
    CTX_USER.reset(tokens[1])
    CTX_USER_ID.reset(tokens[0])


@pytest_asyncio.fixture(loop_scope="session")
async def perm_env(app):
    """每个测试独占 TEST_ROLE 的缓存 key，并在结束时清理。"""
    redis = app.state.redis
    key = f"role:{TEST_ROLE}:apis"
    await redis.delete(key)
    yield app, redis
    await redis.delete(key)


@pytest.mark.asyncio(loop_scope="session")
async def test_grant_exact_route_allows_access(perm_env):
    """对 app 中每个 (method, path_format)，授予精确权限后应放行。"""
    app, redis = perm_env
    routes = list(_all_routes(app))
    assert routes, "expected at least one APIRoute in test app"

    for method, path_format, route in routes:
        await _set_role_apis(redis, TEST_ROLE, [(method, path_format)])
        tokens = _bind_ctx([TEST_ROLE])
        try:
            req = _build_request(app, route, method)
            # 不抛异常即表示通过
            await PermissionControl.has_permission(req, current_user=None)  # type: ignore[arg-type]
        finally:
            _reset_ctx(tokens)


@pytest.mark.asyncio(loop_scope="session")
async def test_no_permission_denies_access(perm_env):
    """对 app 中每个 (method, path_format)，未授予任何权限时应拒绝。"""
    app, redis = perm_env
    await _set_role_apis(redis, TEST_ROLE, [])

    for method, _path_format, route in _all_routes(app):
        tokens = _bind_ctx([TEST_ROLE])
        try:
            req = _build_request(app, route, method)
            with pytest.raises(BizError) as exc_info:
                await PermissionControl.has_permission(req, current_user=None)  # type: ignore[arg-type]
            assert exc_info.value.code == Code.PERMISSION_DENIED
        finally:
            _reset_ctx(tokens)


@pytest.mark.asyncio(loop_scope="session")
async def test_disabled_permission_returns_api_disabled(perm_env):
    """授予但状态为 disable 的 API 应返回 API_DISABLED，而不是放行也不是 PERMISSION_DENIED。"""
    app, redis = perm_env
    method, path_format, route = next(iter(_all_routes(app)))
    payload = [{"method": method, "path": path_format, "status": StatusType.disable.value}]
    await redis.set(f"role:{TEST_ROLE}:apis", json.dumps(payload))

    tokens = _bind_ctx([TEST_ROLE])
    try:
        req = _build_request(app, route, method)
        with pytest.raises(BizError) as exc_info:
            await PermissionControl.has_permission(req, current_user=None)  # type: ignore[arg-type]
        assert exc_info.value.code == Code.API_DISABLED
    finally:
        _reset_ctx(tokens)


@pytest.mark.asyncio(loop_scope="session")
async def test_parametric_permission_does_not_leak_to_static_sibling(perm_env):
    """核心回归：持有 `/resources/{id}` 权限不应自动获得 `/resources/<static>` 的权限。

    旧实现用 re.sub("\\{.*?}", "[^/]+") + re.match 对原始 URL 做匹配，导致
    `/resources/{id}` 权限会命中 `/resources/sync` 之类的静态兄弟路径。
    """
    app, redis = perm_env

    # 在 app 内找一对同 method、同前缀但 "静态段 vs 参数段" 的兄弟路由
    pairs: list[tuple[tuple[str, str, APIRoute], tuple[str, str, APIRoute]]] = []
    by_method: dict[str, list[tuple[str, APIRoute]]] = {}
    for m, p, r in _all_routes(app):
        by_method.setdefault(m, []).append((p, r))

    for m, entries in by_method.items():
        for i, (pi, ri) in enumerate(entries):
            for j, (pj, rj) in enumerate(entries):
                if i == j or pi == pj:
                    continue
                # 同父前缀，同深度，其中一个末段是参数，另一个是静态
                parts_i = pi.rstrip("/").split("/")
                parts_j = pj.rstrip("/").split("/")
                if len(parts_i) != len(parts_j) or parts_i[:-1] != parts_j[:-1]:
                    continue
                last_i, last_j = parts_i[-1], parts_j[-1]
                is_param_i = last_i.startswith("{") and last_i.endswith("}")
                is_param_j = last_j.startswith("{") and last_j.endswith("}")
                if is_param_i and not is_param_j:
                    pairs.append(((m, pi, ri), (m, pj, rj)))
                elif is_param_j and not is_param_i:
                    pairs.append(((m, pj, rj), (m, pi, ri)))

    if not pairs:
        pytest.skip("app 中未发现 `/x/{id}` 与 `/x/<static>` 同级兄弟路由对")

    for (m, param_path, _param_route), (_, static_path, static_route) in pairs:
        await _set_role_apis(redis, TEST_ROLE, [(m, param_path)])
        tokens = _bind_ctx([TEST_ROLE])
        try:
            req = _build_request(app, static_route, m)
            with pytest.raises(BizError) as exc_info:
                await PermissionControl.has_permission(req, current_user=None)  # type: ignore[arg-type]
            assert exc_info.value.code == Code.PERMISSION_DENIED, f"持有 {m.upper()} {param_path} 权限竟然放行了 {m.upper()} {static_path}"
        finally:
            _reset_ctx(tokens)
