"""Aggregate operations. All mutations lock the ticket and use one database transaction."""

from decimal import Decimal
from typing import Any, cast

from tortoise import Tortoise
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.transactions import in_transaction

from app.business.weighbridge_settlement.calculation import calculate
from app.business.weighbridge_settlement.models import SettlementRate, WeighingLine, WeighingTicket
from app.business.weighbridge_settlement.schemas import OrderLookup, PreviewInput, WeighingTicketCreate, WeighingTicketUpdate
from app.utils import BaseModel, BizError, encode_id, get_current_user_id, get_db_conn, radar_log, to_camel_case


def order_model() -> type[BaseModel]:
    # Registered model access keeps the business module import boundary intact.
    return cast(type[BaseModel], Tortoise.apps["app_system"]["Order"])


async def serialize(obj: BaseModel, fields: tuple[str, ...] | None = None) -> dict[str, Any]:
    data = await obj.to_dict(include_fields=list(fields) if fields else None)
    # Keep settlement decimals lossless at the HTTP boundary, without changing global serialization.
    for key in fields or obj._meta.db_fields:
        value = getattr(obj, key)
        if isinstance(value, Decimal):
            places = getattr(obj._meta.fields_map[key], "decimal_places", None)
            data[to_camel_case(key)] = format(value, f".{places}f") if places is not None else format(value, "f")
    return data


async def detail(ticket_id: int, db: BaseDBAsyncClient | None = None) -> dict[str, Any]:
    if db is None:
        async with in_transaction(get_db_conn(WeighingTicket)) as connection:
            return await detail(ticket_id, connection)
    ticket = await WeighingTicket.filter(id=ticket_id).using_db(db).select_for_update().first()
    if ticket is None:
        raise BizError(code="4602", msg="磅单不存在")
    data = await serialize(ticket)
    data["lines"] = [await serialize(line) for line in await WeighingLine.filter(ticket_id=ticket_id).using_db(db).order_by("position")]
    return data


async def locked_ticket(ticket_id: int, revision: int | None, db: BaseDBAsyncClient) -> WeighingTicket:
    ticket = await WeighingTicket.filter(id=ticket_id).using_db(db).select_for_update().first()
    if ticket is None:
        raise BizError(code="4602", msg="磅单不存在")
    if ticket.is_settled:
        raise BizError(code="4603", msg="已结算磅单不可修改或删除")
    if revision is not None and ticket.revision != revision:
        raise BizError(code="4604", msg="磅单已被其他用户修改，请重新加载")
    return ticket


async def save_ticket(payload: WeighingTicketCreate | WeighingTicketUpdate, ticket_id: int | None = None) -> dict[str, Any]:
    async with in_transaction(get_db_conn(WeighingTicket)) as db:
        ticket = await locked_ticket(ticket_id, payload.revision, db) if ticket_id is not None and isinstance(payload, WeighingTicketUpdate) else None
        existing = {row.id: row for row in await WeighingLine.filter(ticket_id=ticket.id).using_db(db)} if ticket else {}
        rate = None
        if ticket is None or payload.rate_id is not None:
            rate = await SettlementRate.filter(id=payload.rate_id, enabled=True).using_db(db).select_for_update().first()
            if rate is None:
                raise BizError(code="4605", msg="请选择已启用的工序")
        if rate:
            price, process = rate.price, rate.process_name
        elif ticket:
            price, process = ticket.price, ticket.process
        else:
            raise BizError(code="4605", msg="请选择已启用的工序")
        rows: list[dict[str, Any]] = []
        ids: set[int] = set()
        orders: set[int] = set()
        for item in payload.lines:
            old = existing.get(item.id) if item.id else None
            if item.id is not None:
                if old is None or item.id in ids:
                    raise BizError(code="4606", msg="明细不属于当前磅单或重复提交")
                ids.add(item.id)
            row = item.model_dump(exclude={"id"})
            if item.order_id is not None:
                if item.order_id in orders:
                    raise BizError(code="4606", msg="同一磅单不能重复选择相同订单")
                orders.add(item.order_id)
                if old and old.order_id == item.order_id:
                    row.update({key: getattr(old, key) for key in ("order_no", "part_no", "name", "net_weight", "gross_weight")})
                    # Historical snapshots may have no usable gross weight; allow filling it once.
                    if old.gross_weight is None or old.gross_weight <= 0:
                        row["gross_weight"] = item.gross_weight
                else:
                    order = await order_model().filter(id=item.order_id).using_db(db).first()
                    if order is None:
                        raise BizError(code="4607", msg="所选订单不存在")
                    row.update({key: getattr(order, key) for key in ("order_no", "part_no", "name", "net_weight", "gross_weight")})
            elif not item.part_no or not item.name:
                raise BizError(code="4601", msg="手动录入需要项目号及名称")
            row["id"] = item.id
            rows.append(row)
        amount, rows = calculate(payload.weight, price, rows)
        actor = str(get_current_user_id() or "")
        values: dict[str, Any] = dict(ticket_no=payload.ticket_no, weighing_date=payload.weighing_date, weight=payload.weight, price=price, process=process, total_amount=amount, updated_by=actor)
        # Older clients omit images; preserve existing attachments unless explicitly submitted.
        if ticket is None or "images" in payload.model_fields_set:
            values["images"] = payload.images
        if rate:
            values["rate_id"] = rate.id
        if ticket:
            # CAS complements row locks (also works on SQLite, where SELECT FOR UPDATE is a no-op).
            changed = await WeighingTicket.filter(id=ticket.id, revision=ticket.revision, is_settled=False).using_db(db).update(**values, revision=ticket.revision + 1)
            if changed != 1:
                raise BizError(code="4604", msg="磅单版本冲突，请重新加载")
            await WeighingLine.filter(ticket_id=ticket.id).exclude(id__in=list(ids)).using_db(db).delete()
            # Free unique (ticket, position/order) slots before reordering or exchanging selected orders.
            for old in existing.values():
                if old.id in ids:
                    await WeighingLine.filter(id=old.id).using_db(db).update(position=-old.id, order_id=None)
        else:
            ticket = await WeighingTicket.create(**values, created_by=actor, using_db=db)
        for row in rows:
            line_id = row.pop("id")
            if line_id is None:
                await WeighingLine.create(ticket_id=ticket.id, **row, created_by=actor, updated_by=actor, using_db=db)
            else:
                old = existing[line_id]
                old.update_from_dict({**row, "updated_by": actor})
                await old.save(using_db=db)
        result = await detail(ticket.id, db)
    radar_log("保存磅单", data={"ticketId": encode_id(ticket.id), "revision": result["revision"]})
    return result


async def settle_ticket(ticket_id: int, revision: int) -> dict[str, Any]:
    async with in_transaction(get_db_conn(WeighingTicket)) as db:
        ticket = await locked_ticket(ticket_id, revision, db)
        if not await SettlementRate.filter(id=ticket.rate_id).using_db(db).exists():
            raise BizError(code="4605", msg="磅单工序不存在")
        lines = await WeighingLine.filter(ticket_id=ticket.id).using_db(db).order_by("position")
        amount, computed = calculate(ticket.weight, ticket.price, [{key: getattr(line, key) for key in ("gross_weight", "quantity")} for line in lines])
        fields = ("theoretical_weight", "allocated_weight", "amount", "tax_unit_price")
        if amount != ticket.total_amount or any(getattr(line, key) != row[key] for line, row in zip(lines, computed, strict=True) for key in fields):
            raise BizError(code="4608", msg="明细分摊不一致，请先编辑并保存磅单")
        changed = (
            await WeighingTicket.filter(id=ticket.id, revision=revision, is_settled=False).using_db(db).update(is_settled=True, revision=revision + 1, updated_by=str(get_current_user_id() or ""))
        )
        if changed != 1:
            raise BizError(code="4604", msg="磅单版本冲突，请重新加载")
        result = await detail(ticket.id, db)
    radar_log("确认磅单结算", data={"ticketId": encode_id(ticket_id)})
    return result


async def delete_tickets(ids: list[int]) -> None:
    async with in_transaction(get_db_conn(WeighingTicket)) as db:
        for ticket_id in sorted(set(ids)):
            await locked_ticket(ticket_id, None, db)
        await WeighingTicket.filter(id__in=ids, is_settled=False).using_db(db).delete()
    radar_log("删除未结算磅单", data={"ticketIds": [encode_id(value) for value in ids]})


async def rate_options() -> list[dict[str, Any]]:
    return [await serialize(rate) for rate in await SettlementRate.filter(enabled=True).order_by("process_name")]


async def order_options(query: OrderLookup) -> list[dict[str, Any]]:
    model = order_model()
    fields = ("id", "part_no", "order_no", "name", "net_weight", "gross_weight")
    exact = await model.filter(part_no=query.part_no).order_by("id").limit(query.limit).only(*fields)
    remaining = query.limit - len(exact)
    partial = await model.filter(part_no__icontains=query.part_no).exclude(part_no=query.part_no).order_by("part_no", "id").limit(remaining).only(*fields) if remaining else []
    return [await serialize(order, fields) for order in [*exact, *partial]]


def preview(query: PreviewInput) -> dict[str, Any]:
    amount, rows = calculate(query.weight, query.price, [line.model_dump(exclude={"id", "order_id"}) for line in query.lines])
    return {"totalAmount": str(amount), "lines": [{to_camel_case(key): format(value, "f") if isinstance(value, Decimal) else value for key, value in row.items()} for row in rows]}
