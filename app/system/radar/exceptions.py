from __future__ import annotations

import sys
import traceback
from types import TracebackType


def format_exception_pretty(
    exc_type: type[BaseException] | None = None,
    exc_value: BaseException | None = None,
    exc_tb: TracebackType | None = None,
) -> str:
    if exc_type is None:
        exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_type is None:
        return ""
    # 标准 traceback 不包含局部变量，避免密码、令牌等运行时值进入 Radar。
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
