"""Tests for Radar API endpoints (app/radar/api.py)."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.cache import load_role_permissions, refresh_user_roles
from app.core.code import Code
from app.core.config import APP_SETTINGS
from app.system.init_data import RADAR_API_REFS
from app.system.models import Api, Menu, Role, User
from app.system.radar import api as radar_api
from app.system.radar import db as radar_db
from app.system.radar.ctx import RadarRequestContext
from app.system.radar.db import flush_request_data
from app.system.radar.models import RadarQuery, RadarRequest, RadarUserLog
from app.system.radar.redaction import REDACTED
from app.system.schemas.login import JWTPayload
from app.system.security import create_access_token, get_password_hash
from app.system.services import monitor

pytestmark = pytest.mark.asyncio(loop_scope="session")

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature"


@pytest.fixture
def client(auth_client: AsyncClient) -> AsyncClient:
    """Radar functional tests use the existing authenticated super-admin client."""
    return auth_client


def _access_token(user: User) -> str:
    now = datetime.now(UTC)
    return create_access_token(
        data=JWTPayload(
            data={"userId": user.id, "userName": user.user_name, "tokenType": "accessToken", "tokenVersion": user.token_version},
            iat=now,
            exp=now + timedelta(minutes=APP_SETTINGS.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )
    )


@pytest.fixture(scope="session")
async def seed_radar_api_data(app):
    """Seed radar data for API tests."""
    req1 = await RadarRequest.create(
        x_request_id="api-req-001",
        method="GET",
        path="/downloads/token/path-legacy-secret",
        client_ip="127.0.0.1",
        query_params=f"page=1&access_token={JWT}",
        request_headers={"authorization": f"Bearer {JWT}", "content-type": "application/json"},
        request_body='{"userName":"tester","password":"legacy-password"}',
        response_status=200,
        response_headers={"set-cookie": f"session={JWT}"},
        response_body=f'{{"code":"0000","msg":"token={JWT}","data":{{"token":"{JWT}"}}}}',
        duration_ms=25.0,
    )
    req2 = await RadarRequest.create(
        x_request_id="api-req-002",
        method="POST",
        path="/api/v1/auth/login",
        client_ip="10.0.0.1",
        response_status=200,
        response_body='{"code":"0000","msg":"OK"}',
        duration_ms=60.0,
    )
    req_err = await RadarRequest.create(
        x_request_id="api-req-err-001",
        method="DELETE",
        path="/api/v1/danger",
        client_ip="10.0.0.2",
        response_status=500,
        response_body='{"code":"5000","msg":"Error"}',
        duration_ms=300.0,
        error_type="ValueError",
        error_message="bad value",
        error_traceback="Traceback ... password=legacy-password",
    )
    await RadarQuery.create(request=req1, sql_text="SELECT 1", params='["legacy-password"]', operation="SELECT", duration_ms=2.0, start_offset_ms=1.0)
    await RadarQuery.create(
        request=req1,
        sql_text="SELECT 2",
        params="[password=legacy-password parameters redacted]",
        operation="SELECT",
        duration_ms=3.0,
        start_offset_ms=2.0,
    )
    await RadarQuery.create(
        request=req1,
        sql_text="SELECT 'sql-legacy-secret'",
        params=None,
        operation="SELECT",
        duration_ms=4.0,
        start_offset_ms=3.0,
    )
    await RadarQuery.create(request=req1, sql_text="SELECT * FROM big_table", operation="SELECT", duration_ms=200.0, start_offset_ms=5.0)
    await RadarUserLog.create(request=req1, level="INFO", message=f"token={JWT}", data='{"password":"legacy-password","code":"0000"}', offset_ms=3.0)

    return {"req1": req1, "req2": req2, "req_err": req_err}


async def test_storage_boundary_redacts_new_records_and_preserves_business_fields(app):
    context = RadarRequestContext(
        x_request_id="storage-redaction-001",
        method="POST",
        path="/downloads/session/storage-path-secret",
        query_params=f"page=1&access_token={JWT}",
        request_headers={"authorization": f"Bearer {JWT}", "x-safe": "visible"},
        request_body='{"password":"storage-secret","code":"0000"}',
        response_headers={"set-cookie": f"session={JWT}"},
        response_body=f'{{"code":"0000","msg":"OK","data":{{"refreshToken":"{JWT}"}}}}',
        response_status=200,
        exception_info={"type": "RuntimeError", "message": f"token={JWT}", "traceback": "password=trace-secret"},
    )
    context.queries.append({
        "sql": "SELECT * FROM users WHERE token = 'storage-sql-secret'",
        "params": "[1 parameters redacted]",
        "operation": "SELECT",
        "duration_ms": 1.5,
        "connection_name": "default",
        "start_offset_ms": 0.5,
    })
    context.user_logs.append({
        "level": "INFO",
        "message": f"Bearer {JWT}",
        "data": '{"password":"log-secret","msg":"OK"}',
        "source": "test",
        "offset_ms": 0.7,
    })

    await flush_request_data(context)

    stored = await RadarRequest.get(x_request_id=context.x_request_id)
    stored_query = await RadarQuery.get(request=stored)
    stored_log = await RadarUserLog.get(request=stored)
    serialized = json.dumps({
        "query": stored.query_params,
        "request_headers": stored.request_headers,
        "request_body": stored.request_body,
        "response_headers": stored.response_headers,
        "response_body": stored.response_body,
        "error_message": stored.error_message,
        "error_traceback": stored.error_traceback,
        "query_params": stored_query.params,
        "log_message": stored_log.message,
        "log_data": stored_log.data,
    })

    assert JWT not in serialized
    assert "storage-secret" not in serialized
    assert "trace-secret" not in serialized
    assert "log-secret" not in serialized
    assert "storage-path-secret" not in stored.path
    assert "storage-sql-secret" not in stored_query.sql_text
    assert json.loads(stored.request_body)["code"] == "0000"
    assert json.loads(stored.response_body)["msg"] == "OK"
    assert stored_query.params == "[1 parameters redacted]"


async def test_storage_failure_log_does_not_include_context_or_exception_values(monkeypatch):
    messages: list[str] = []

    async def fail_create(**kwargs):
        raise RuntimeError("exception-secret")

    class CapturingLogger:
        @staticmethod
        def error(message, *args):
            messages.append(message.format(*args))

    monkeypatch.setattr(RadarRequest, "create", fail_create)
    monkeypatch.setattr(radar_db, "logger", CapturingLogger())

    await flush_request_data(
        RadarRequestContext(
            x_request_id="storage-failure-001",
            request_body='{"password":"context-secret"}',
        )
    )

    assert messages == ["Failed to flush radar data (RuntimeError)"]
    assert "exception-secret" not in messages[0]
    assert "context-secret" not in messages[0]


class TestAuthorization:
    async def test_anonymous_read_and_purge_are_denied_without_side_effects(self, app):
        marker, _ = await RadarRequest.get_or_create(
            x_request_id="anonymous-purge-marker",
            defaults={"method": "GET", "path": "/security-marker"},
        )
        await RadarRequest.filter(id=marker.id).update(created_at=datetime.now() - timedelta(days=2))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as anonymous:
            read_response = await anonymous.get("/__radar/api/requests")
            purge_response = await anonymous.delete("/__radar/api/purge", params={"retention_hours": 1})

        assert read_response.json()["code"] == Code.INVALID_TOKEN
        assert purge_response.json()["code"] == Code.INVALID_TOKEN
        assert await RadarRequest.filter(id=marker.id).exists()

    async def test_r_user_is_denied_and_r_admin_and_r_super_are_allowed(self, app, seed_data, client, monkeypatch):
        async def ensure_user(user_name: str, role_code: str) -> User:
            user = await User.filter(user_name=user_name).first()
            if user is None:
                user = await User.create(user_name=user_name, password=get_password_hash("test-password"))
            role = await Role.get(role_code=role_code)
            await user.by_user_roles.clear()
            await user.by_user_roles.add(role)
            await refresh_user_roles(app.state.redis, user.id)
            return user

        admin_role = await Role.get(role_code="R_ADMIN")
        custom_role = await Role.filter(role_code="R_RADAR_CUSTOM").first()
        if custom_role is None:
            custom_role = await Role.create(
                role_name="Radar custom role",
                role_code="R_RADAR_CUSTOM",
                by_role_home=await Menu.get(route_name="home"),
            )
        for method, path in RADAR_API_REFS:
            api = await Api.filter(api_method=method, api_path=path).first()
            if api is None:
                api = await Api.create(api_method=method, api_path=path, summary="Radar test API", tags=["Radar"], is_system=True)
            await admin_role.by_role_apis.add(api)
            await custom_role.by_role_apis.add(api)

        regular_user = await ensure_user("radar_regular_user", "R_USER")
        admin_user = await ensure_user("radar_admin_user", "R_ADMIN")
        custom_user = await ensure_user("radar_custom_user", "R_RADAR_CUSTOM")
        await load_role_permissions(app.state.redis)
        marker = await RadarRequest.create(x_request_id="regular-purge-marker", method="GET", path="/security-marker")
        await RadarRequest.filter(id=marker.id).update(created_at=datetime.now() - timedelta(days=2))

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {_access_token(regular_user)}"},
        ) as regular_client:
            denied = await regular_client.get("/__radar/api/requests")
            denied_purge = await regular_client.delete("/__radar/api/purge", params={"retention_hours": 1})
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {_access_token(custom_user)}"},
        ) as custom_client:
            custom_denied = await custom_client.get("/__radar/api/requests")

        monkeypatch.setattr(radar_api.collector, "get_overview", lambda: {})
        monkeypatch.setattr(radar_api.collector, "get_realtime", lambda: {})
        monkeypatch.setattr(APP_SETTINGS, "APP_DEBUG", False)

        authorized_calls = [
            ("get", "/__radar/api/requests", {}),
            ("get", "/__radar/api/requests/missing", {}),
            ("get", "/__radar/api/queries", {}),
            ("get", "/__radar/api/exceptions", {}),
            ("put", "/__radar/api/exceptions/missing/resolve", {"json": {"resolved": True}}),
            ("get", "/__radar/api/stats", {}),
            ("get", "/__radar/api/dashboard", {}),
            ("delete", "/__radar/api/purge", {"params": {"retention_hours": 999999}}),
            ("get", "/__radar/api/monitor/overview", {}),
            ("get", "/__radar/api/monitor/realtime", {}),
        ]

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {_access_token(admin_user)}"},
        ) as admin_client:
            for method, path, kwargs in authorized_calls:
                allowed = await admin_client.request(method, path, **kwargs)
                assert allowed.json()["code"] not in {Code.INVALID_TOKEN, Code.PERMISSION_DENIED, Code.API_DISABLED}
            admin_boom = await admin_client.get("/__radar/api/_boom")

        for method, path, kwargs in authorized_calls:
            allowed = await client.request(method, path, **kwargs)
            assert allowed.json()["code"] not in {Code.INVALID_TOKEN, Code.PERMISSION_DENIED, Code.API_DISABLED}
        super_boom = await client.get("/__radar/api/_boom")

        assert denied.json()["code"] == Code.PERMISSION_DENIED
        assert denied_purge.json()["code"] == Code.PERMISSION_DENIED
        assert custom_denied.json()["code"] == Code.NEED_ANY_ROLE
        assert await RadarRequest.filter(id=marker.id).exists()
        assert admin_boom.json()["code"] == Code.PERMISSION_DENIED
        assert super_boom.json()["code"] == "2200"


class TestListRequests:
    async def test_default(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == "0000"
        assert data["data"]["total"] >= 3
        assert len(data["data"]["records"]) >= 3
        assert "legacy-password" not in resp.text
        assert JWT not in resp.text
        for record in data["data"]["records"]:
            assert "requestHeaders" not in record
            assert "requestBody" not in record
            assert "responseHeaders" not in record
            assert "responseBody" not in record
            assert "errorTraceback" not in record

    async def test_with_path_filter(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests", params={"path_filter": "/downloads/token"})
        data = resp.json()
        assert data["code"] == "0000"
        assert all("/downloads/token" in r["path"] for r in data["data"]["records"])

    async def test_with_code_filter(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests", params={"code_filter": "5000"})
        data = resp.json()
        assert data["code"] == "0000"
        assert data["data"]["total"] >= 1

    async def test_with_min_duration(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests", params={"min_duration": 100})
        data = resp.json()
        assert data["code"] == "0000"
        assert all(r["durationMs"] >= 100 for r in data["data"]["records"])

    async def test_with_has_error(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests", params={"has_error": True})
        data = resp.json()
        assert data["code"] == "0000"
        assert data["data"]["total"] >= 1

    async def test_pagination(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests", params={"page": 1, "page_size": 1})
        data = resp.json()
        assert len(data["data"]["records"]) == 1
        assert data["data"]["current"] == 1
        assert data["data"]["size"] == 1

    async def test_page_size_validation(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests", params={"page_size": 200})
        data = resp.json()
        # Exceeds le=100 validation — FastAPI RequestValidationError wraps into 1200
        assert resp.status_code == 200
        assert data["code"] == Code.REQUEST_VALIDATION


class TestRequestDetail:
    async def test_found(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests/api-req-001")
        data = resp.json()
        assert data["code"] == "0000"
        detail = data["data"]
        assert detail["xRequestId"] == "api-req-001"
        assert "queries" in detail
        assert "user_logs" in detail
        assert len(detail["queries"]) >= 2
        assert len(detail["user_logs"]) >= 1
        assert "legacy-password" not in resp.text
        assert "path-legacy-secret" not in resp.text
        assert "sql-legacy-secret" not in resp.text
        assert JWT not in resp.text
        assert json.loads(detail["requestBody"])["password"] == REDACTED
        assert json.loads(detail["responseBody"])["data"]["token"] == REDACTED
        assert detail["businessMsg"] == f"token={REDACTED}"
        assert detail["requestHeaders"]["authorization"] == REDACTED
        assert detail["responseHeaders"]["set-cookie"] == REDACTED
        assert detail["queries"][0]["params"] == REDACTED
        assert json.loads(detail["user_logs"][0]["data"])["password"] == REDACTED

    async def test_not_found(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/requests/nonexistent-id")
        data = resp.json()
        assert data["code"] == "4004"
        assert data["data"] is None


class TestListQueries:
    async def test_default(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/queries")
        data = resp.json()
        assert data["code"] == "0000"
        assert data["data"]["total"] >= 2
        assert "legacy-password" not in resp.text
        assert all(record["params"] in {None, REDACTED} or record["params"].endswith(" parameters redacted]") for record in data["data"]["records"])

    async def test_slow_only(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/queries", params={"slow_only": True, "threshold_ms": 100})
        data = resp.json()
        assert data["code"] == "0000"
        assert data["data"]["total"] >= 1
        assert all(r["durationMs"] >= 100 for r in data["data"]["records"])

    async def test_records_include_request_info(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/queries")
        records = resp.json()["data"]["records"]
        for r in records:
            assert "xRequestId" in r
            assert "requestPath" in r


class TestListExceptions:
    async def test_default(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/exceptions")
        data = resp.json()
        assert data["code"] == "0000"
        assert data["data"]["total"] >= 1
        for r in data["data"]["records"]:
            assert r.get("errorType") is not None
        assert "legacy-password" not in resp.text

    async def test_filter_by_path(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/exceptions", params={"path_filter": "danger"})
        data = resp.json()
        assert data["data"]["total"] >= 1

    async def test_filter_by_error_type(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/exceptions", params={"error_type": "ValueError"})
        data = resp.json()
        assert data["data"]["total"] >= 1

    async def test_filter_by_resolved(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/exceptions", params={"resolved": False})
        data = resp.json()
        assert data["data"]["total"] >= 1


class TestResolveException:
    async def test_resolve(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.put("/__radar/api/exceptions/api-req-err-001/resolve", json={"resolved": True})
        data = resp.json()
        assert data["code"] == "0000"

        # Verify resolved
        req = await RadarRequest.get(x_request_id="api-req-err-001")
        assert req.resolved is True

    async def test_unresolve(self, client: AsyncClient, seed_radar_api_data):
        await RadarRequest.filter(x_request_id="api-req-err-001").update(resolved=True)
        resp = await client.put("/__radar/api/exceptions/api-req-err-001/resolve", json={"resolved": False})
        data = resp.json()
        assert data["code"] == "0000"

    async def test_resolve_not_found(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.put("/__radar/api/exceptions/nonexistent/resolve", json={"resolved": True})
        data = resp.json()
        assert data["code"] == "4004"

    async def test_resolve_missing_body(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.put("/__radar/api/exceptions/api-req-err-001/resolve")
        # Missing body — app exception handler wraps validation error
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == Code.REQUEST_VALIDATION


class TestStats:
    async def test_default(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/stats")
        data = resp.json()
        assert data["code"] == "0000"
        stats = data["data"]
        assert stats["request_count"] >= 3
        assert "avg_duration_ms" in stats
        assert "error_count" in stats
        assert "error_rate" in stats
        assert "query_count" in stats
        assert "slow_query_count" in stats
        assert "user_log_count" in stats

    async def test_with_hours(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/stats", params={"hours": 1})
        data = resp.json()
        assert data["code"] == "0000"


class TestDashboard:
    async def test_default(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/dashboard")
        data = resp.json()
        assert data["code"] == "0000"
        stats = data["data"]
        assert "total_requests" in stats
        assert "avg_response_time" in stats
        assert "total_queries" in stats
        assert "total_exceptions" in stats
        assert "success_rate" in stats
        assert "error_rate" in stats
        assert "rps" in stats
        assert "p50" in stats
        assert "p95" in stats
        assert "p99" in stats
        assert "distribution" in stats
        assert "response_time_trend" in stats
        assert "query_activity" in stats

    async def test_with_hours(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/dashboard", params={"hours": 24})
        data = resp.json()
        assert data["code"] == "0000"
        assert isinstance(data["data"]["response_time_trend"], list)
        assert isinstance(data["data"]["query_activity"], list)

    async def test_distribution_has_codes(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.get("/__radar/api/dashboard", params={"hours": 1})
        dist = resp.json()["data"]["distribution"]
        assert isinstance(dist, list)
        if dist:
            assert "code" in dist[0]
            assert "count" in dist[0]


class TestMonitor:
    async def test_realtime_uses_process_snapshot(self, client: AsyncClient, monkeypatch):
        class FakeProcess:
            def __init__(self, pid: int) -> None:
                self.pid = pid

            def oneshot(self):
                return self

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def status(self) -> str:
                return monitor.psutil.STATUS_RUNNING if self.pid == 101 else monitor.psutil.STATUS_SLEEPING

            def create_time(self) -> float:
                return 1_700_000_000.0

            def cpu_percent(self, interval=None) -> float:
                return float(self.pid)

            def memory_percent(self) -> float:
                return self.pid / 10

            def name(self) -> str:
                return f"proc-{self.pid}"

        def fail_process_iter(*args, **kwargs):
            raise AssertionError("process_iter should not be used by realtime monitor")

        monkeypatch.setattr(monitor.collector, "_process_snapshot", None)
        monkeypatch.setattr(monitor.collector, "_process_snapshot_time", 0)
        monkeypatch.setattr(monitor.psutil, "pids", lambda: [101, 102, 103])
        monkeypatch.setattr(monitor.psutil, "Process", FakeProcess)
        monkeypatch.setattr(monitor.psutil, "process_iter", fail_process_iter)

        resp = await client.get("/__radar/api/monitor/realtime")
        data = resp.json()

        assert resp.status_code == 200
        assert data["code"] == "0000"
        assert data["data"]["system_status"]["total_processes"] == 3
        assert data["data"]["system_status"]["running_processes"] == 1
        assert data["data"]["system_status"]["sleeping_processes"] == 2
        assert [proc["pid"] for proc in data["data"]["top_processes"]] == [103, 102, 101]


class TestPurge:
    async def test_purge(self, client: AsyncClient, seed_radar_api_data):
        resp = await client.delete("/__radar/api/purge", params={"retention_hours": 24})
        data = resp.json()
        assert data["code"] == "0000"
        assert "deleted_count" in data["data"]
        assert isinstance(data["data"]["deleted_count"], int)

    async def test_purge_all_old_data(self, client: AsyncClient, app):
        """Purge with short retention should not delete just-created data."""
        await RadarRequest.create(
            x_request_id="purge-test-001",
            method="GET",
            path="/purge-test",
        )
        resp = await client.delete("/__radar/api/purge", params={"retention_hours": 1})
        data = resp.json()
        assert data["code"] == "0000"
        # Just-created data should still exist
        exists = await RadarRequest.filter(x_request_id="purge-test-001").exists()
        assert exists is True
