import json

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.system.init_data import RADAR_API_REFS
from app.system.radar import setup_radar
from app.system.radar.config import RADAR_SETTINGS
from app.system.radar.ctx import CTX_RADAR, RadarRequestContext
from app.system.radar.developer import radar_log
from app.system.radar.exceptions import format_exception_pretty
from app.system.radar.middleware import RadarMiddleware
from app.system.radar.query_capture import _serialize_params
from app.system.radar.redaction import REDACTED, redact_headers, redact_path, redact_query_string, redact_sql, redact_text, redact_value

pytestmark = pytest.mark.asyncio(loop_scope="session")

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature"


async def test_auth_path_is_never_captured_even_when_included(monkeypatch):
    observed_contexts = []

    async def inner(scope, receive, send):
        observed_contexts.append(CTX_RADAR.get())
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b'{"code":"0000"}'})

    monkeypatch.setattr(RADAR_SETTINGS, "RADAR_INCLUDE_PATHS", ["/api/v1/auth/login"])
    async with AsyncClient(transport=ASGITransport(app=RadarMiddleware(inner)), base_url="http://testserver") as client:
        response = await client.post("/api/v1/auth/login", json={"userName": "admin", "password": "plain-secret"})

    assert response.status_code == 200
    assert observed_contexts == [None]


async def test_deep_redaction_preserves_business_codes_and_masks_validation_input():
    payload = {
        "code": "0000",
        "msg": "OK",
        "data": {
            "password": "plain-secret",
            "refresh_token": JWT,
            "currentPassword": "current-secret",
            "password_confirmation": "confirmation-secret",
            "authToken": "opaque-token",
            "nested": [{"clientSecret": "client-secret"}],
        },
        "validation": {"loc": ["body", "newPassword"], "input": "invalid-secret"},
        "raw": f"Bearer {JWT}".encode(),
    }

    redacted = redact_value(payload)

    assert redacted["code"] == "0000"
    assert redacted["msg"] == "OK"
    assert redacted["data"]["password"] == REDACTED
    assert redacted["data"]["refresh_token"] == REDACTED
    assert redacted["data"]["currentPassword"] == REDACTED
    assert redacted["data"]["password_confirmation"] == REDACTED
    assert redacted["data"]["authToken"] == REDACTED
    assert redacted["data"]["nested"][0]["clientSecret"] == REDACTED
    assert redacted["validation"]["input"] == REDACTED
    assert redacted["raw"] == f"Bearer {REDACTED}"


async def test_json_form_query_headers_and_inline_tokens_are_redacted():
    json_body = redact_text(json.dumps({"code": "0000", "token": JWT, "profile": {"password": "plain-secret"}}))
    form_body = redact_text("username=admin&password=plain-secret&remember=true")
    query = redact_query_string(f"page=1&access_token={JWT}")
    headers = redact_headers({
        "authorization": f"Bearer {JWT}",
        "proxy-authorization": "Basic dXNlcjpwcm94eS1zZWNyZXQ=",
        "set-cookie": f"session={JWT}",
        "x-trace": JWT,
    })
    basic_assignment = redact_text("proxy-authorization=Basic dXNlcjpwcm94eS1zZWNyZXQ=")

    assert json_body is not None
    parsed = json.loads(json_body)
    assert parsed == {"code": "0000", "token": REDACTED, "profile": {"password": REDACTED}}
    assert "plain-secret" not in (form_body or "")
    assert "plain-secret" not in (query or "")
    assert JWT not in (query or "")
    assert REDACTED in (form_body or "")
    assert REDACTED in (query or "")
    assert headers == {
        "authorization": REDACTED,
        "proxy-authorization": REDACTED,
        "set-cookie": REDACTED,
        "x-trace": REDACTED,
    }
    assert basic_assignment == f"proxy-authorization={REDACTED}"


async def test_multipart_sensitive_fields_are_redacted_without_changing_business_code():
    multipart = '--boundary\r\nContent-Disposition: form-data; name="password"\r\n\r\nplain-secret\r\n--boundary\r\nContent-Disposition: form-data; name="code"\r\n\r\n0000\r\n--boundary--\r\n'

    redacted = redact_text(multipart)

    assert redacted is not None
    assert "plain-secret" not in redacted
    assert f' name="password"\r\n\r\n{REDACTED}' in redacted
    assert ' name="code"\r\n\r\n0000' in redacted


async def test_xml_paths_and_sql_literals_are_redacted():
    xml = '<request apiKey="attribute-secret"><profile><password>xml-secret</password></profile><code>0000</code></request>'

    redacted_xml = redact_text(xml)
    redacted_param_path = redact_path("/downloads/opaque-path-secret", path_params={"sessionToken": "opaque-path-secret"})
    redacted_marker_path = redact_path("/downloads/session/marker-path-secret")
    redacted_query = redact_sql("SELECT * FROM users WHERE token = 'sql-secret' /* comment-secret */")

    assert redacted_xml is not None
    assert "attribute-secret" not in redacted_xml
    assert "xml-secret" not in redacted_xml
    assert "<code>0000</code>" in redacted_xml
    assert redacted_param_path == f"/downloads/{REDACTED}"
    assert redacted_marker_path == f"/downloads/session/{REDACTED}"
    assert "sql-secret" not in redacted_query
    assert "comment-secret" not in redacted_query
    assert REDACTED in redacted_query


async def test_setup_radar_mounts_only_when_enabled(monkeypatch):
    disabled_app = FastAPI()
    monkeypatch.setattr(RADAR_SETTINGS, "RADAR_ENABLED", False)
    setup_radar(disabled_app)
    assert not any(route.path.startswith("/__radar/api") for route in disabled_app.routes)

    enabled_app = FastAPI()
    monkeypatch.setattr(RADAR_SETTINGS, "RADAR_ENABLED", True)
    setup_radar(enabled_app)
    mounted_routes = {(method.lower(), route.path) for route in enabled_app.routes for method in getattr(route, "methods", set())}

    assert set(RADAR_API_REFS).issubset(mounted_routes)
    assert ("get", "/__radar/api/_boom") in mounted_routes


async def test_radar_log_redacts_file_and_timeline_sinks(monkeypatch):
    file_messages: list[str] = []
    monkeypatch.setitem(__import__("app.system.radar.developer", fromlist=["_LOG_DISPATCH"])._LOG_DISPATCH, "INFO", file_messages.append)
    context = RadarRequestContext(x_request_id="redaction-test")
    token = CTX_RADAR.set(context)
    try:
        radar_log(f"token={JWT}", data={"password": "plain-secret", "code": "0000"})
    finally:
        CTX_RADAR.reset(token)

    assert len(file_messages) == 1
    assert JWT not in file_messages[0]
    assert "plain-secret" not in file_messages[0]
    assert REDACTED in file_messages[0]
    assert context.user_logs[0]["message"] == f"token={REDACTED}"
    assert json.loads(context.user_logs[0]["data"]) == {"password": REDACTED, "code": "0000"}


async def test_sql_params_and_exception_locals_do_not_retain_values():
    assert _serialize_params(["plain-secret", JWT]) == "[2 parameters redacted]"
    assert _serialize_params("plain-secret") == REDACTED

    try:
        password = "trace-local-secret"
        assert password
        raise RuntimeError("safe failure")
    except RuntimeError as exc:
        rendered = format_exception_pretty(type(exc), exc, exc.__traceback__)

    assert "trace-local-secret" not in rendered
    assert "safe failure" in rendered
