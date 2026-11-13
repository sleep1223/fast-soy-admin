"""Order matching bounded by production unit and exact part numbers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from functools import reduce
from operator import or_
from typing import Any, Literal

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q

from app.business.work_ticket_management.models import MatchSource, MatchStatus, OrderUnitMapping
from app.business.work_ticket_management.rules import normalize_part_no
from app.business.work_ticket_management.services.order_access import order_model


@dataclass(frozen=True)
class Candidate:
    order: Any
    mapping_status: Literal["confirmed", "other_unit", "unconfirmed"]
    mapped_units: tuple[str, ...] = ()


@dataclass(frozen=True)
class MatchDecision:
    status: MatchStatus
    order_id: int | None = None
    source: MatchSource = MatchSource.none
    candidate_count: int = 0
    candidates: tuple[Candidate, ...] = field(default_factory=tuple)


async def load_mappings(order_ids: list[int], db: BaseDBAsyncClient) -> dict[int, dict[int, str]]:
    """Return order_id -> {unit_id: unit_name} for the given orders."""
    if not order_ids:
        return {}
    mappings = await OrderUnitMapping.filter(order_id__in=order_ids).using_db(db).prefetch_related("production_unit")
    result: dict[int, dict[int, str]] = defaultdict(dict)
    for mapping in mappings:
        unit = mapping.production_unit
        if unit is not None:
            result[mapping.order_id][unit.id] = unit.name
    return dict(result)


def candidate_from_order(order: Any, production_unit_id: int, mappings: dict[int, dict[int, str]]) -> Candidate:
    units = mappings.get(order.id, {})
    if production_unit_id in units:
        status: Literal["confirmed", "other_unit", "unconfirmed"] = "confirmed"
    elif units:
        status = "other_unit"
    else:
        status = "unconfirmed"
    return Candidate(order=order, mapping_status=status, mapped_units=tuple(units.values()))


async def load_orders_by_part(part_nos: set[str], db: BaseDBAsyncClient) -> dict[str, list[Any]]:
    """Bulk exact match first, then case-insensitive exact match for misses."""
    values = sorted(value for value in part_nos if value)
    result: dict[str, list[Any]] = defaultdict(list)
    if not values:
        return {}
    orders = await order_model().filter(part_no__in=values).using_db(db)
    found: set[str] = set()
    for order in orders:
        key = normalize_part_no(getattr(order, "part_no", ""))
        result[key].append(order)
        found.add(str(getattr(order, "part_no", "")))
    missing = [value for value in values if value not in found]
    for batch in (missing[index : index + 200] for index in range(0, len(missing), 200)):
        query = reduce(or_, (Q(part_no__iexact=value) for value in batch))
        extra = await order_model().filter(query).using_db(db)
        for order in extra:
            key = normalize_part_no(getattr(order, "part_no", ""))
            if order.id not in {item.id for item in result[key]}:
                result[key].append(order)
    return dict(result)


async def decide_matches(
    rows: list[tuple[int, str]],
    production_unit_id: int,
    db: BaseDBAsyncClient,
) -> dict[int, MatchDecision]:
    """Match (row key, normalized part no) pairs; never uses contains matching."""
    parts = {normalized for _, normalized in rows if normalized}
    orders_by_part = await load_orders_by_part(parts, db)
    order_ids = list({order.id for orders in orders_by_part.values() for order in orders})
    mappings = await load_mappings(order_ids, db)
    decisions: dict[int, MatchDecision] = {}
    for row_key, normalized in rows:
        if not normalized or len(normalized) > 200:
            decisions[row_key] = MatchDecision(status=MatchStatus.invalid, source=MatchSource.none)
            continue
        orders = orders_by_part.get(normalized, [])
        candidates = [candidate_from_order(order, production_unit_id, mappings) for order in orders]
        current = [candidate for candidate in candidates if candidate.mapping_status == "confirmed"]
        if len(current) == 1:
            decisions[row_key] = MatchDecision(
                status=MatchStatus.matched,
                order_id=current[0].order.id,
                source=MatchSource.auto,
                candidate_count=len(candidates),
                candidates=tuple(candidates),
            )
        elif len(current) > 1:
            decisions[row_key] = MatchDecision(
                status=MatchStatus.ambiguous,
                source=MatchSource.none,
                candidate_count=len(candidates),
                candidates=tuple(candidates),
            )
        elif len(candidates) == 1:
            status = MatchStatus.other_unit if candidates[0].mapping_status == "other_unit" else MatchStatus.unassigned
            decisions[row_key] = MatchDecision(
                status=status,
                source=MatchSource.none,
                candidate_count=1,
                candidates=tuple(candidates),
            )
        elif len(candidates) > 1:
            decisions[row_key] = MatchDecision(
                status=MatchStatus.ambiguous,
                source=MatchSource.none,
                candidate_count=len(candidates),
                candidates=tuple(candidates),
            )
        else:
            decisions[row_key] = MatchDecision(status=MatchStatus.missing, source=MatchSource.none)
    return decisions


async def candidates(
    part_no: str,
    production_unit_id: int,
    *,
    include_other_units: bool,
    include_partial: bool,
    limit: int,
    db: BaseDBAsyncClient,
) -> list[Candidate]:
    normalized = normalize_part_no(part_no)
    exact: list[Any] = []
    seen: set[int] = set()
    if normalized:
        for order in await order_model().filter(part_no=part_no).using_db(db):
            exact.append(order)
            seen.add(order.id)
        for order in await order_model().filter(part_no__iexact=normalized).using_db(db):
            if order.id not in seen:
                exact.append(order)
                seen.add(order.id)
    partial: list[Any] = []
    if include_partial and len(exact) < limit and normalized:
        for order in await order_model().filter(part_no__icontains=part_no).using_db(db).order_by("part_no", "id").limit(limit * 2):
            if order.id not in seen:
                partial.append(order)
                seen.add(order.id)
    mappings = await load_mappings([order.id for order in [*exact, *partial]], db)
    result: list[Candidate] = []
    for order in [*exact, *partial]:
        candidate = candidate_from_order(order, production_unit_id, mappings)
        if not include_other_units and candidate.mapping_status == "other_unit":
            continue
        result.append(candidate)
        if len(result) >= limit:
            break
    return result
