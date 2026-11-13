"""Thin API helpers shared by workflow routers."""

from __future__ import annotations

from base64 import b64encode
from typing import Any

from app.core.base_schema import Success, SuccessExtra


def dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    if isinstance(value, list):
        return [dump(item) for item in value]
    return value


def page(records: list[Any], total: int, current: int, size: int) -> SuccessExtra:
    return SuccessExtra(data={"records": dump(records)}, total=total, current=current, size=size)


def excel_file(filename: str, content: bytes) -> Success:
    return Success(data={"filename": filename, "content": b64encode(content).decode()})


__all__ = ["dump", "excel_file", "page"]
