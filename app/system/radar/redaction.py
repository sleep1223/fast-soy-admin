from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode

REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = frozenset({
    "password",
    "passwd",
    "pwd",
    "oldpassword",
    "newpassword",
    "confirmpassword",
    "rawpassword",
    "token",
    "accesstoken",
    "refreshtoken",
    "idtoken",
    "authorization",
    "cookie",
    "setcookie",
    "apikey",
    "xapikey",
    "xauthtoken",
    "csrftoken",
    "secret",
    "clientsecret",
    "secretkey",
    "otp",
    "captcha",
    "verificationcode",
    "smscode",
})

_SENSITIVE_KEY_PARTS = frozenset({"password", "passwd", "pwd", "token", "secret", "cookie", "otp", "captcha", "authorization", "session", "credential"})
_SENSITIVE_PATH_MARKERS = frozenset({
    "password",
    "resetpassword",
    "token",
    "tokens",
    "session",
    "sessions",
    "apikey",
    "secret",
    "credential",
    "credentials",
    "invite",
    "invitation",
    "verify",
    "verification",
    "magic",
    "magiclink",
})
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_INLINE_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?P<key>[a-z][a-z0-9_.-]{0,63})(?P<separator>\s*[:=]\s*)"
    r"(?:(?P<quote>[\"'])(?P<quoted>[^\r\n]*)(?P=quote)|(?P<unquoted>(?:(?:bearer|basic)\s+)?[^\"'\s,;&}\r\n]+))"
)
_MULTIPART_FIELD_RE = re.compile(
    r"(?is)(?P<prefix>content-disposition:[^\r\n]*\bname=(?P<quote>[\"'])(?P<key>[^\"']+)(?P=quote)[^\r\n]*\r?\n"
    r"(?:[^\r\n]+\r?\n)*\r?\n)(?P<value>.*?)(?=\r?\n--[^\r\n]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_BASIC_AUTH_RE = re.compile(r"(?i)\bBasic\s+[A-Za-z0-9+/=]+")
_JWT_RE = re.compile(r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])")
_XML_ELEMENT_RE = re.compile(r"(?is)(?P<open><(?P<tag>(?:[a-z_][\w.-]*:)?[a-z_][\w.-]*)\b[^>]*>)(?P<value>.*?)(?P<close></(?P=tag)\s*>)")
_SQL_BLOCK_COMMENT_RE = re.compile(r"(?s)/\*.*?\*/")
_SQL_LINE_COMMENT_RE = re.compile(r"(?m)--[^\r\n]*")
_SQL_DOLLAR_QUOTED_RE = re.compile(r"(?s)(?P<delimiter>\$(?:[a-zA-Z_][a-zA-Z0-9_]*)?\$).*?(?P=delimiter)")
_SQL_STRING_LITERAL_RE = re.compile(r"(?is)(?P<prefix>[enbx]?)(?P<literal>'(?:''|\\.|[^'])*')")


def _normalize_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def is_sensitive_key(key: object) -> bool:
    normalized = _normalize_key(key)
    if normalized in _SENSITIVE_KEYS:
        return True

    expanded = _CAMEL_BOUNDARY_RE.sub("_", str(key))
    parts = set(re.findall(r"[a-z0-9]+", expanded.lower()))
    return bool(parts & _SENSITIVE_KEY_PARTS) or ({"api", "key"} <= parts) or normalized in {"privatekey", "signingkey", "csrf", "xsrf", "xsrftoken"}


def _redact_inline_secrets(text: str) -> str:
    def replace_assignment(match: re.Match[str]) -> str:
        if not is_sensitive_key(match.group("key")):
            return match.group(0)
        quote = match.group("quote") or ""
        return f"{match.group('key')}{match.group('separator')}{quote}{REDACTED}{quote}"

    text = _INLINE_ASSIGNMENT_RE.sub(replace_assignment, text)
    text = _BEARER_RE.sub(f"Bearer {REDACTED}", text)
    text = _BASIC_AUTH_RE.sub(f"Basic {REDACTED}", text)
    return _JWT_RE.sub(REDACTED, text)


def _redact_multipart(text: str) -> str:
    def replace_field(match: re.Match[str]) -> str:
        if not is_sensitive_key(match.group("key")):
            return match.group(0)
        return f"{match.group('prefix')}{REDACTED}"

    return _MULTIPART_FIELD_RE.sub(replace_field, text)


def _redact_xml(text: str, *, depth: int = 0) -> str:
    if depth >= 20:
        return REDACTED

    def replace_element(match: re.Match[str]) -> str:
        local_name = match.group("tag").rsplit(":", 1)[-1]
        if is_sensitive_key(local_name):
            return f"{match.group('open')}{REDACTED}{match.group('close')}"
        nested = _redact_xml(match.group("value"), depth=depth + 1)
        return f"{match.group('open')}{nested}{match.group('close')}"

    return _XML_ELEMENT_RE.sub(replace_element, text)


def redact_path(path: str | None, *, path_params: Mapping[str, object] | None = None) -> str | None:
    if path is None or not path:
        return path

    segments = path.split("/")
    if path_params:
        sensitive_values: set[str] = set()
        for name, value in path_params.items():
            if is_sensitive_key(name) or _normalize_key(name) in _SENSITIVE_PATH_MARKERS:
                raw_value = str(value)
                sensitive_values.update({raw_value, quote(raw_value, safe="")})
        segments = [REDACTED if segment in sensitive_values else segment for segment in segments]

    redact_next = False
    for index, segment in enumerate(segments):
        if not segment:
            continue
        if redact_next:
            segments[index] = REDACTED
            redact_next = False
            continue
        normalized = _normalize_key(segment)
        if normalized in _SENSITIVE_PATH_MARKERS or is_sensitive_key(segment):
            redact_next = True

    return _redact_inline_secrets("/".join(segments))


def redact_sql(sql: str) -> str:
    sql = _SQL_BLOCK_COMMENT_RE.sub(f"/* {REDACTED} */", sql)
    sql = _SQL_LINE_COMMENT_RE.sub(f"-- {REDACTED}", sql)
    sql = _SQL_DOLLAR_QUOTED_RE.sub(lambda match: f"{match.group('delimiter')}{REDACTED}{match.group('delimiter')}", sql)
    sql = _SQL_STRING_LITERAL_RE.sub(lambda match: f"{match.group('prefix')}'{REDACTED}'", sql)
    return _redact_inline_secrets(sql)


def redact_value(value: Any, *, key: object | None = None) -> Any:
    """Return a deep, non-mutating copy with security-sensitive values removed."""
    if key is not None and is_sensitive_key(key):
        return REDACTED

    if isinstance(value, Mapping):
        location = value.get("loc")
        sensitive_validation_input = isinstance(location, Sequence) and not isinstance(location, (str, bytes, bytearray)) and bool(location) and is_sensitive_key(location[-1])
        result: dict[Any, Any] = {}
        for item_key, item_value in value.items():
            if item_key == "input" and sensitive_validation_input:
                result[item_key] = REDACTED
            else:
                result[item_key] = redact_value(item_value, key=item_key)
        return result

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_value(item) for item in value]

    if isinstance(value, (bytes, bytearray)):
        return redact_text(bytes(value).decode("utf-8", errors="replace"))

    if isinstance(value, str):
        return redact_text(value)

    return value


def redact_text(text: str | None) -> str | None:
    if text is None or not text:
        return text

    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            return json.dumps(redact_value(parsed), ensure_ascii=False, separators=(",", ":"), default=str)

    if "=" in text and "&" in text:
        pairs = parse_qsl(text, keep_blank_values=True)
        if pairs:
            return urlencode([(name, REDACTED if is_sensitive_key(name) else _redact_inline_secrets(value)) for name, value in pairs], safe="[]")

    return _redact_inline_secrets(_redact_multipart(_redact_xml(text)))


def redact_query_string(query: str | None) -> str | None:
    if query is None or not query:
        return query
    pairs = parse_qsl(query, keep_blank_values=True)
    if not pairs:
        return _redact_inline_secrets(query)
    return urlencode([(name, REDACTED if is_sensitive_key(name) else _redact_inline_secrets(value)) for name, value in pairs], safe="[]")


def redact_headers(headers: Mapping[str, str] | None) -> dict[str, str] | None:
    if headers is None:
        return None
    return {name: REDACTED if is_sensitive_key(name) else _redact_inline_secrets(value) for name, value in headers.items()}


__all__ = ["REDACTED", "is_sensitive_key", "redact_headers", "redact_path", "redact_query_string", "redact_sql", "redact_text", "redact_value"]
