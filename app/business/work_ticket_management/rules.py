"""纯业务规则：项目号、工票码、月份和 OCR 候选解析。"""

from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Callable

YEAR_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")
WHITESPACE_RE = re.compile(r"\s+")
NUMERIC_OCR_TOKEN_RE = re.compile(r"[0-9OoIlSs]{3,100}")
GENERAL_OCR_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{2,99}")
OCR_CONFUSIONS = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "|": "1", "S": "5", "s": "5"})


class RuleError(ValueError):
    """A pure rule rejected the input."""


@dataclass(frozen=True)
class OrderSnapshot:
    order_no: str
    part_no: str
    name: str
    net_weight: object | None = None
    gross_weight: object | None = None
    process_route: str | None = None
    quantity: int | None = None
    received_quantity: int | None = None


@dataclass(frozen=True)
class TicketCodeRule:
    """A verified mapping from order data to a work-ticket code.

    Rules are intentionally registered in code, not guessed at runtime. The
    samples are the acceptance contract: a rule whose samples fail must not be
    used to create tickets.
    """

    name: str
    version: str
    description: str
    pattern: re.Pattern[str]
    transform: Callable[[OrderSnapshot, int], str]
    samples: tuple[tuple[str, str], ...] = ()

    def preview(self, order: OrderSnapshot, sequence: int = 1) -> str:
        code = self.transform(order, sequence).strip()
        if not code or len(code) > 100 or not self.pattern.fullmatch(code):
            raise RuleError(f"工票码规则 {self.name} 生成的结果不符合格式: {code!r}")
        return code

    def validate(self, code: str) -> bool:
        return bool(code) and len(code) <= 100 and bool(self.pattern.fullmatch(code))

    def validate_samples(self) -> None:
        for order_no, expected in self.samples:
            actual = self.preview(OrderSnapshot(order_no=order_no, part_no="", name=""), 1)
            if actual != expected:
                raise RuleError(f"工票码规则 {self.name} 样本不匹配: {order_no} -> {actual!r}, 期望 {expected!r}")


RULE_REGISTRY: dict[str, TicketCodeRule] = {}


def register_rule(rule: TicketCodeRule) -> None:
    rule.validate_samples()
    RULE_REGISTRY[rule.name] = rule


def get_rule(name: str | None = None) -> TicketCodeRule | None:
    if name:
        return RULE_REGISTRY.get(name)
    if len(RULE_REGISTRY) == 1:
        return next(iter(RULE_REGISTRY.values()))
    return None


def normalize_part_no(raw: object) -> str:
    text = unicodedata.normalize("NFKC", str(raw or ""))
    text = ZERO_WIDTH_RE.sub("", text).strip()
    return WHITESPACE_RE.sub(" ", text).upper()


def normalize_ticket_code(raw: str | None) -> tuple[str | None, str | None]:
    """Return (display value, comparison key). Leading zeros are preserved."""
    if raw is None:
        return None, None
    display = unicodedata.normalize("NFKC", raw).strip()
    if not display:
        return None, None
    key = WHITESPACE_RE.sub("", display).upper()
    return display[:100], key[:100]


def validate_ticket_code(code: str | None, rule: TicketCodeRule | None = None) -> tuple[str | None, str | None]:
    display, key = normalize_ticket_code(code)
    if display is None:
        return None, None
    if rule is not None and not rule.validate(display):
        raise RuleError(f"工票码不符合规则 {rule.name}")
    if any(ord(char) < 32 for char in display):
        raise RuleError("工票码不能包含控制字符")
    return display, key


def parse_year_month(value: str) -> tuple[int, int]:
    match = YEAR_MONTH_RE.fullmatch(value)
    if not match:
        raise RuleError("月份格式必须为 YYYY-MM")
    return int(match.group(1)), int(match.group(2))


def month_start(value: str) -> date:
    year, month = parse_year_month(value)
    return date(year, month, 1)


def month_end(value: str) -> date:
    year, month = parse_year_month(value)
    return date(year, month, calendar.monthrange(year, month)[1])


def month_of_date(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def effective_accounting_month(ticket_month: str, override: str | None) -> str:
    return override or ticket_month


def normalize_ocr_token(token: str, numeric_mode: bool = True) -> str:
    cleaned = unicodedata.normalize("NFKC", token).strip()
    cleaned = WHITESPACE_RE.sub("", cleaned)
    if numeric_mode:
        cleaned = cleaned.translate(OCR_CONFUSIONS)
        cleaned = re.sub(r"[^0-9]", "", cleaned)
    return cleaned


def extract_ocr_tokens(text: str, numeric_mode: bool = True) -> list[tuple[str, str]]:
    """Extract de-duplicated (original, normalized) candidates from OCR text."""
    pattern = NUMERIC_OCR_TOKEN_RE if numeric_mode else GENERAL_OCR_TOKEN_RE
    result: list[tuple[str, str]] = []
    for line in text.splitlines():
        for match in pattern.finditer(line):
            original = match.group(0)
            normalized = normalize_ocr_token(original, numeric_mode=numeric_mode)
            if len(normalized) < 3:
                continue
            result.append((original, normalized))
    return result
