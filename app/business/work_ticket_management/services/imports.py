"""Monthly Excel/manual imports, preview matching and row corrections."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.business.work_ticket_management.models import (
    HandlingStatus,
    ImportBatchStatus,
    ImportSourceType,
    MatchSource,
    MatchStatus,
    MonthlyImportBatch,
    MonthlyImportRow,
    TicketStatus,
    WorkTicket,
)
from app.business.work_ticket_management.rules import normalize_part_no
from app.business.work_ticket_management.schemas_workflow import (
    ImportBatchVoidIn,
    ImportCommitOut,
    ImportPreviewOut,
    ImportPreviewRow,
    ImportRowBatchMatchIn,
    ImportRowIgnoreIn,
    ImportRowMatchIn,
    ImportRowOut,
    ImportRowSearchIn,
    ImportRowUpdateIn,
    ManualImportIn,
)
from app.business.work_ticket_management.services.common import actor_name, lock_month, sqid, start_month_if_draft
from app.business.work_ticket_management.services.master_data import ensure_order_mapping, get_month_unit
from app.business.work_ticket_management.services.matching import MatchDecision, decide_matches
from app.business.work_ticket_management.services.order_access import get_order, order_model
from app.core.excel import ExcelColumn, ExcelConfig, ExcelImportOptions, parse_excel
from app.utils import BizError, Code, SchemaBase, get_db_conn, radar_log


# A lenient schema: invalid part numbers/quantities are stored and marked, not dropped.
class ImportRowInput(SchemaBase):
    raw_part_no: Any = ""
    source_quantity: Any = None


IMPORT_EXCEL = ExcelConfig(
    fields=("raw_part_no", "source_quantity"),
    columns={
        "raw_part_no": ExcelColumn(title="项目号", aliases=("件号", "项目号", "partNo", "part_no", "项目")),
        "source_quantity": ExcelColumn(title="数量", aliases=("数量", "件数", "重量", "qty", "quantity")),
    },
)


@dataclass
class ParsedRow:
    row_number: int
    raw_part_no: str
    normalized_part_no: str
    source_quantity: Decimal | None
    note: str | None = None


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def _parse_quantity(value: Any) -> tuple[Decimal | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, None
    try:
        number = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None, "来源数量无法识别"
    if not number.is_finite() or number < 0:
        return None, "来源数量必须为非负数"
    return number.quantize(Decimal("0.001")), None


def _parse_excel_rows(content: bytes, options: ExcelImportOptions | None) -> tuple[list[ParsedRow], list[str]]:
    result = parse_excel(content, ImportRowInput, IMPORT_EXCEL, options)  # type: ignore[arg-type]
    rows: list[ParsedRow] = []
    for row_number, item in result.rows:
        raw = _cell_text(item.raw_part_no)  # type: ignore[attr-defined]
        normalized = normalize_part_no(raw)
        quantity, quantity_note = _parse_quantity(item.source_quantity)  # type: ignore[attr-defined]
        note = quantity_note
        if not raw:
            note = "项目号为空"
        elif len(normalized) > 200:
            note = "项目号超过 200 字符"
        if note and quantity_note and note != quantity_note:
            note = f"{note}；{quantity_note}"
        rows.append(ParsedRow(row_number=row_number, raw_part_no=raw, normalized_part_no=normalized, source_quantity=quantity, note=note))
    return rows, list(result.preview.errors)


async def _orders_by_id(order_ids: list[int], db: BaseDBAsyncClient) -> dict[int, Any]:
    if not order_ids:
        return {}
    orders = await order_model().filter(id__in=order_ids).using_db(db)
    return {order.id: order for order in orders}


def _preview_row(parsed: ParsedRow, decision: MatchDecision, order: Any, duplicate_of: int | None, duplicate_in_file: bool) -> ImportPreviewRow:
    note = parsed.note
    if duplicate_in_file and not duplicate_of:
        note = "文件内重复" if not note else f"{note}；文件内重复"
    status = MatchStatus.invalid if parsed.note == "项目号为空" or len(parsed.normalized_part_no) > 200 else decision.status
    return ImportPreviewRow(
        row_number=parsed.row_number,
        raw_part_no=parsed.raw_part_no,
        normalized_part_no=parsed.normalized_part_no,
        match_status=status,
        match_source=decision.source.value,
        order_id=sqid(decision.order_id),
        order_no=getattr(order, "order_no", None) if order else None,
        part_no=getattr(order, "part_no", None) if order else None,
        name=getattr(order, "name", None) if order else None,
        candidate_count=decision.candidate_count,
        duplicate_of_row_id=sqid(duplicate_of),
        note=note,
    )


async def _build_preview(month_id: int, source_type: ImportSourceType, parsed: list[ParsedRow], errors: list[str], db: BaseDBAsyncClient) -> ImportPreviewOut:
    _, unit = await get_month_unit(month_id, db)
    decisions = await decide_matches([(index, row.normalized_part_no) for index, row in enumerate(parsed)], unit.id, db)
    order_ids = [decision.order_id for decision in decisions.values() if decision.order_id is not None]
    orders = await _orders_by_id(list(set(order_ids)), db)
    normalized_values = [row.normalized_part_no for row in parsed if row.normalized_part_no]
    existing_first: dict[str, int] = {}
    if normalized_values:
        existing = (
            await MonthlyImportRow
            .filter(
                batch__work_month_id=month_id,
                batch__source_type=source_type,
                batch__status=ImportBatchStatus.active,
                normalized_part_no__in=normalized_values,
            )
            .using_db(db)
            .order_by("id")
            .values("id", "normalized_part_no")
        )
        for row in existing:
            existing_first.setdefault(row["normalized_part_no"], row["id"])
    within_first: dict[str, int] = {}
    rows_out: list[ImportPreviewRow] = []
    duplicate_rows = 0
    matched_rows = 0
    ambiguous_rows = 0
    missing_rows = 0
    invalid_rows = 0
    for index, row in enumerate(parsed):
        decision = decisions[index]
        duplicate_of = existing_first.get(row.normalized_part_no)
        duplicate_in_file = row.normalized_part_no in within_first
        within_first.setdefault(row.normalized_part_no, 0)
        preview = _preview_row(row, decision, orders.get(decision.order_id) if decision.order_id else None, duplicate_of, duplicate_in_file)
        if preview.duplicate_of_row_id or duplicate_in_file:
            duplicate_rows += 1
        if preview.match_status == MatchStatus.invalid:
            invalid_rows += 1
        elif preview.match_status == MatchStatus.matched:
            matched_rows += 1
        elif preview.match_status == MatchStatus.ambiguous:
            ambiguous_rows += 1
        else:
            missing_rows += 1
        rows_out.append(preview)
    return ImportPreviewOut(
        source_type=source_type,
        rows=rows_out[:500],
        errors=errors,
        total_rows=len(parsed),
        invalid_rows=invalid_rows,
        duplicate_rows=duplicate_rows,
        matched_rows=matched_rows,
        ambiguous_rows=ambiguous_rows,
        missing_rows=missing_rows,
        truncated=len(rows_out) > 500,
    )


async def preview_import(work_month_id: int, source_type: ImportSourceType, content: bytes, options: ExcelImportOptions | None) -> ImportPreviewOut:
    parsed, errors = await asyncio.to_thread(_parse_excel_rows, content, options)
    if not parsed:
        errors.append("没有可导入的数据")
    async with in_transaction(get_db_conn(MonthlyImportRow)) as db:
        return await _build_preview(work_month_id, source_type, parsed, errors, db)


async def _batch_counts(batch_id: int, db: BaseDBAsyncClient) -> ImportCommitOut:
    rows = MonthlyImportRow.filter(batch_id=batch_id).using_db(db)
    total = await rows.count()
    invalid = await rows.filter(match_status=MatchStatus.invalid).count()
    duplicate = await rows.exclude(duplicate_of_row_id__isnull=True).count()
    matched = await rows.filter(match_status=MatchStatus.matched).count()
    ambiguous = await rows.filter(match_status=MatchStatus.ambiguous).count()
    missing = await rows.filter(match_status__in=[MatchStatus.missing, MatchStatus.unassigned, MatchStatus.other_unit]).count()
    return ImportCommitOut(
        batch_id=sqid(batch_id),
        row_count=total,
        invalid_rows=invalid,
        duplicate_rows=duplicate,
        matched_rows=matched,
        ambiguous_rows=ambiguous,
        missing_rows=missing,
    )


async def _commit_parsed(
    work_month_id: int,
    source_type: ImportSourceType,
    parsed: list[ParsedRow],
    *,
    source_name: str | None,
    content_hash: str | None,
) -> ImportCommitOut:
    if not parsed:
        raise BizError(code=Code.REQUEST_VALIDATION, msg="没有可导入的数据")
    actor = actor_name()
    async with in_transaction(get_db_conn(MonthlyImportBatch)) as db:
        month = await lock_month(work_month_id, db)
        if content_hash:
            existing = (
                await MonthlyImportBatch
                .filter(
                    work_month_id=work_month_id,
                    source_type=source_type,
                    status=ImportBatchStatus.active,
                    content_hash=content_hash,
                )
                .using_db(db)
                .first()
            )
            if existing is not None:
                return await _batch_counts(existing.id, db)
        _, unit = await get_month_unit(work_month_id, db)
        decisions = await decide_matches([(index, row.normalized_part_no) for index, row in enumerate(parsed)], unit.id, db)
        normalized_values = [row.normalized_part_no for row in parsed if row.normalized_part_no]
        existing_first: dict[str, int] = {}
        if normalized_values:
            existing_rows = (
                await MonthlyImportRow
                .filter(
                    batch__work_month_id=work_month_id,
                    batch__source_type=source_type,
                    batch__status=ImportBatchStatus.active,
                    normalized_part_no__in=normalized_values,
                )
                .using_db(db)
                .order_by("id")
                .values("id", "normalized_part_no")
            )
            for row in existing_rows:
                existing_first.setdefault(row["normalized_part_no"], row["id"])
        batch = await MonthlyImportBatch.create(
            work_month_id=work_month_id,
            source_type=source_type,
            status=ImportBatchStatus.active,
            source_name=(source_name.replace("\\", "/").split("/")[-1][:255] if source_name else None),
            content_hash=content_hash,
            row_count=len(parsed),
            created_by=actor,
            updated_by=actor,
            using_db=db,
        )
        await start_month_if_draft(month, db, actor)
        first_by_normalized = dict(existing_first)
        invalid_rows = duplicate_rows = matched_rows = ambiguous_rows = missing_rows = 0
        for index, row in enumerate(parsed):
            decision = decisions[index]
            duplicate_of = first_by_normalized.get(row.normalized_part_no)
            status = MatchStatus.invalid if row.note == "项目号为空" or len(row.normalized_part_no) > 200 else decision.status
            created = await MonthlyImportRow.create(
                batch_id=batch.id,
                row_number=row.row_number,
                raw_part_no=row.raw_part_no[:200] if row.raw_part_no else "",
                normalized_part_no=row.normalized_part_no[:200],
                order_id=decision.order_id if status != MatchStatus.invalid else None,
                match_status=status,
                match_source=decision.source if status != MatchStatus.invalid else MatchSource.none,
                source_quantity=row.source_quantity,
                raw_data={"rawPartNo": row.raw_part_no, "sourceQuantity": str(row.source_quantity) if row.source_quantity is not None else None},
                handling_status=HandlingStatus.open,
                duplicate_of_row_id=duplicate_of,
                note=row.note,
                created_by=actor,
                updated_by=actor,
                using_db=db,
            )
            first_by_normalized.setdefault(row.normalized_part_no, created.id)
            if duplicate_of:
                duplicate_rows += 1
            if status == MatchStatus.invalid:
                invalid_rows += 1
            elif status == MatchStatus.matched:
                matched_rows += 1
            elif status == MatchStatus.ambiguous:
                ambiguous_rows += 1
            else:
                missing_rows += 1
        radar_log("导入工票月度清单", data={"batchId": batch.id, "sourceType": source_type.value, "rows": len(parsed)})
    return ImportCommitOut(
        batch_id=sqid(batch.id),
        row_count=len(parsed),
        invalid_rows=invalid_rows,
        duplicate_rows=duplicate_rows,
        matched_rows=matched_rows,
        ambiguous_rows=ambiguous_rows,
        missing_rows=missing_rows,
    )


async def commit_import(
    work_month_id: int,
    source_type: ImportSourceType,
    content: bytes,
    options: ExcelImportOptions | None,
    source_name: str | None,
) -> ImportCommitOut:
    parsed, errors = await asyncio.to_thread(_parse_excel_rows, content, options)
    if errors:
        raise BizError(code=Code.REQUEST_VALIDATION, msg=errors[0])
    return await _commit_parsed(work_month_id, source_type, parsed, source_name=source_name, content_hash=hashlib.sha256(content).hexdigest())


async def manual_import(payload: ManualImportIn) -> ImportCommitOut:
    parsed = [
        ParsedRow(
            row_number=index,
            raw_part_no=row.raw_part_no,
            normalized_part_no=normalize_part_no(row.raw_part_no),
            source_quantity=row.source_quantity,
            note=None if row.raw_part_no else "项目号为空",
        )
        for index, row in enumerate(payload.rows, start=1)
    ]
    return await _commit_parsed(payload.work_month_id, payload.source_type, parsed, source_name=payload.source_name or "手工补录", content_hash=None)


async def void_batch(batch_id: int, payload: ImportBatchVoidIn) -> None:
    actor = actor_name()
    async with in_transaction(get_db_conn(MonthlyImportBatch)) as db:
        batch = await MonthlyImportBatch.filter(id=batch_id).using_db(db).select_for_update().first()
        if batch is None:
            raise BizError(code=Code.WORK_IMPORT_BATCH_NOT_FOUND, msg="导入批次不存在")
        month = await lock_month(batch.work_month_id, db)
        if batch.status != ImportBatchStatus.active:
            raise BizError(code=Code.WORK_ROW_BATCH_NOT_ACTIVE, msg="导入批次已作废")
        row_ids = await MonthlyImportRow.filter(batch_id=batch.id).using_db(db).values_list("id", flat=True)
        if row_ids and await WorkTicket.filter(source_import_row_id__in=row_ids, status=TicketStatus.active).using_db(db).exists():
            raise BizError(code=Code.WORK_IMPORT_HAS_TICKETS, msg="该批次已有工票引用，不能作废；请先处理工票")
        batch.status = ImportBatchStatus.void
        batch.void_reason = payload.reason
        batch.voided_at = datetime.now()
        batch.voided_by = actor
        batch.updated_by = actor
        await batch.save(using_db=db)
        radar_log("作废月度导入批次", data={"batchId": batch.id, "workMonthId": month.id})


async def _row_out(row: MonthlyImportRow, db: BaseDBAsyncClient) -> ImportRowOut:
    batch = await MonthlyImportBatch.filter(id=row.batch_id).using_db(db).first()
    order = await get_order(row.order_id, db) if row.order_id else None
    return ImportRowOut(
        id=sqid(row.id),
        batch_id=sqid(row.batch_id),
        source_type=batch.source_type if batch else ImportSourceType.plan,
        row_number=row.row_number,
        raw_part_no=row.raw_part_no,
        normalized_part_no=row.normalized_part_no,
        order_id=sqid(row.order_id),
        order_no=getattr(order, "order_no", None) if order else None,
        part_no=getattr(order, "part_no", None) if order else None,
        name=getattr(order, "name", None) if order else None,
        match_status=row.match_status,
        match_source=row.match_source.value,
        handling_status=row.handling_status,
        handling_note=row.handling_note,
        duplicate_of_row_id=sqid(row.duplicate_of_row_id),
        source_quantity=row.source_quantity,
        note=row.note,
    )


async def list_rows(search: ImportRowSearchIn) -> tuple[int, list[ImportRowOut]]:
    query = MonthlyImportRow.filter(batch__status=ImportBatchStatus.active)
    if search.work_month_id is not None:
        query = query.filter(batch__work_month_id=search.work_month_id)
    if search.source_type is not None:
        query = query.filter(batch__source_type=search.source_type)
    if search.match_status is not None:
        query = query.filter(match_status=search.match_status)
    if search.handling_status is not None:
        query = query.filter(handling_status=search.handling_status)
    if search.batch_id is not None:
        query = query.filter(batch_id=search.batch_id)
    if search.keyword:
        query = query.filter(Q(raw_part_no__icontains=search.keyword) | Q(normalized_part_no__icontains=search.keyword))
    async with in_transaction(get_db_conn(MonthlyImportRow)) as db:
        total = await query.using_db(db).count()
        rows = await query.using_db(db).order_by("batch_id", "row_number").offset((search.current - 1) * search.size).limit(search.size)
        return total, [await _row_out(row, db) for row in rows]


async def _lock_row(row_id: int, db: BaseDBAsyncClient) -> tuple[MonthlyImportRow, MonthlyImportBatch]:
    row = await MonthlyImportRow.filter(id=row_id).using_db(db).select_for_update().first()
    if row is None:
        raise BizError(code=Code.WORK_IMPORT_ROW_NOT_FOUND, msg="导入行不存在")
    batch = await MonthlyImportBatch.filter(id=row.batch_id).using_db(db).first()
    if batch is None or batch.status != ImportBatchStatus.active:
        raise BizError(code=Code.WORK_ROW_BATCH_NOT_ACTIVE, msg="导入批次已作废")
    return row, batch


async def update_row(row_id: int, payload: ImportRowUpdateIn) -> ImportRowOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(MonthlyImportRow)) as db:
        row, batch = await _lock_row(row_id, db)
        month = await lock_month(batch.work_month_id, db)
        if await WorkTicket.filter(source_import_row_id=row.id, status=TicketStatus.active).using_db(db).exists():
            raise BizError(code=Code.WORK_IMPORT_HAS_TICKETS, msg="该导入行已有工票引用，不能修改项目号")
        if "raw_part_no" in payload.model_fields_set:
            row.raw_part_no = (payload.raw_part_no or "").strip()[:200]
            row.normalized_part_no = normalize_part_no(row.raw_part_no)[:200]
            decision = (await decide_matches([(0, row.normalized_part_no)], month.production_unit_id, db))[0]
            row.order_id = decision.order_id
            row.match_status = MatchStatus.invalid if not row.raw_part_no else decision.status
            row.match_source = decision.source
        if "source_quantity" in payload.model_fields_set:
            row.source_quantity = payload.source_quantity
        if "note" in payload.model_fields_set:
            row.note = payload.note
        row.updated_by = actor
        await row.save(using_db=db)
        return await _row_out(row, db)


async def match_row(row_id: int, payload: ImportRowMatchIn) -> ImportRowOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(MonthlyImportRow)) as db:
        row, batch = await _lock_row(row_id, db)
        month = await lock_month(batch.work_month_id, db)
        order = await get_order(payload.order_id, db)
        if order is None:
            raise BizError(code=Code.WORK_ORDER_NOT_FOUND, msg="订单不存在")
        await ensure_order_mapping(order.id, month.production_unit_id, db, actor, allow_add_mapping=payload.confirm_mapping)
        row.order_id = order.id
        row.match_status = MatchStatus.matched
        row.match_source = MatchSource.manual
        row.handling_status = HandlingStatus.resolved
        row.handled_at = datetime.now()
        row.handled_by = actor
        row.updated_by = actor
        await row.save(using_db=db)
        return await _row_out(row, db)


async def ignore_row(row_id: int, payload: ImportRowIgnoreIn) -> ImportRowOut:
    actor = actor_name()
    async with in_transaction(get_db_conn(MonthlyImportRow)) as db:
        row, batch = await _lock_row(row_id, db)
        await lock_month(batch.work_month_id, db)
        row.handling_status = HandlingStatus.ignored
        row.handling_note = payload.reason
        row.handled_at = datetime.now()
        row.handled_by = actor
        row.updated_by = actor
        await row.save(using_db=db)
        return await _row_out(row, db)


async def batch_match(payload: ImportRowBatchMatchIn) -> dict[str, int]:
    actor = actor_name()
    async with in_transaction(get_db_conn(MonthlyImportRow)) as db:
        month = await lock_month(payload.work_month_id, db)
        query = MonthlyImportRow.filter(batch__work_month_id=payload.work_month_id, batch__status=ImportBatchStatus.active)
        if payload.ids:
            query = query.filter(id__in=payload.ids)
        rows = await query.using_db(db).select_for_update()
        decisions = await decide_matches([(index, row.normalized_part_no) for index, row in enumerate(rows)], month.production_unit_id, db)
        counts: dict[str, int] = {}
        for index, row in enumerate(rows):
            decision = decisions[index]
            row.order_id = decision.order_id
            row.match_status = decision.status
            row.match_source = decision.source
            row.updated_by = actor
            await row.save(using_db=db)
            counts[decision.status.value] = counts.get(decision.status.value, 0) + 1
        return counts
