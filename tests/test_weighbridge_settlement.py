"""Settlement acceptance tests run exclusively against an isolated in-memory database."""

from base64 import b64decode
from collections.abc import AsyncIterator
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openpyxl import load_workbook
from tortoise.context import tortoise_test_context

from app.business.order_management.models import Order
from app.business.weighbridge_settlement import services
from app.business.weighbridge_settlement.api.manage import router
from app.business.weighbridge_settlement.calculation import calculate
from app.business.weighbridge_settlement.models import SettlementRate, WeighingLine, WeighingTicket
from app.business.weighbridge_settlement.schemas import WeighingTicketCreate, WeighingTicketUpdate
from app.core.ctx import CTX_USER_ID
from app.core.dependency import PermissionControl
from app.core.init_app import register_exceptions
from app.utils import BizError, decode_id, encode_id


@pytest.fixture
async def settlement_db():
    async with tortoise_test_context(
        modules=["app.business.order_management.models", "app.business.weighbridge_settlement.models"],
        app_label="app_system",
        connection_label="conn_system",
        use_tz=False,
    ):
        token = CTX_USER_ID.set(1)
        rate = await SettlementRate.create(process_name="喷漆", price=Decimal("2.5000"))
        yield rate
        CTX_USER_ID.reset(token)


def payload(rate, **overrides):
    data = dict(
        ticketNo="T-001",
        weighingDate="2026-11-01",
        weight="100.001",
        rateId=encode_id(rate.id),
        lines=[
            dict(orderId=None, partNo="manual-1", name="手动一", netWeight="1.000001", grossWeight="1.500001", quantity=3),
            dict(orderId=None, partNo="manual-2", name="手动二", netWeight="2.000000", grossWeight="2.500000", quantity=2),
        ],
    )
    return {**data, **overrides}


def edit_payload(detail, **overrides):
    keys = ["id", "orderId", "orderNo", "partNo", "name", "netWeight", "grossWeight", "quantity"]
    return {**{key: detail[key] for key in ["ticketNo", "weighingDate", "weight", "revision"]}, "lines": [{key: line[key] for key in keys} for line in detail["lines"]], **overrides}


@pytest.mark.parametrize("weight,price,count", [("100.001", "2.5000", 3), ("0.002", "99.9999", 30), ("999999.999", "0.0001", 7)])
def test_decimal_residuals(weight, price, count):
    amount, lines = calculate(Decimal(weight), Decimal(price), [dict(gross_weight=Decimal("1.000001"), quantity=3) for _ in range(count)])
    assert sum(row["allocated_weight"] for row in lines) == Decimal(weight)
    assert sum(row["amount"] for row in lines) == amount
    assert all(row["allocated_weight"] >= 0 and row["amount"] >= 0 for row in lines)
    assert amount == (Decimal(weight) * Decimal(price)).quantize(Decimal(".01"), rounding="ROUND_HALF_UP")
    assert [row["position"] for row in lines] == list(range(1, count + 1))


@pytest.mark.asyncio(loop_scope="session")
async def test_manual_and_matched_persistence_snapshot_revision_and_lock(settlement_db):
    rate = settlement_db
    order = await Order.create(order_no="O-1", part_no="P-1", name="原名称", net_weight="3.123456", gross_weight="4.654321", quantity=999)
    data = payload(rate)
    data["lines"].insert(0, dict(orderId=encode_id(order.id), quantity=2))
    saved = await services.save_ticket(WeighingTicketCreate.model_validate(data))
    ticket_id = decode_id(saved["id"])
    assert len(saved["lines"]) == 3
    assert saved["lines"][0]["quantity"] == 2
    assert saved["lines"][0]["netWeight"] == "3.123456"
    assert saved["lines"][0]["grossWeight"] == "4.654321"
    assert saved["lines"][1]["grossWeight"] == "1.500001"
    assert saved["lines"][2]["grossWeight"] == "2.500000"
    assert saved["lines"][1]["theoreticalWeight"] == "4.500003"
    assert all(row["orderId"] is None for row in saved["lines"][1:])
    assert await Order.all().count() == 1
    assert await services.detail(ticket_id) == saved
    await SettlementRate.filter(id=rate.id).update(price=Decimal("9.9999"), enabled=False)
    await Order.filter(id=order.id).update(name="新名称", net_weight="9.000000", gross_weight="10.000000")
    original_ids = [line["id"] for line in saved["lines"]]
    changed = edit_payload(saved, weight="120.001")
    changed["lines"] = list(reversed(changed["lines"]))
    updated = await services.save_ticket(WeighingTicketUpdate.model_validate(changed), ticket_id)
    assert updated["price"] == "2.5" or Decimal(updated["price"]) == Decimal("2.5000")
    assert updated["lines"][-1]["name"] == "原名称"
    assert updated["lines"][-1]["grossWeight"] == "4.654321"
    assert updated["lines"][1]["grossWeight"] == "1.500001"
    assert [line["id"] for line in updated["lines"]] == list(reversed(original_ids))
    with pytest.raises(BizError, match="其他用户"):
        await services.save_ticket(WeighingTicketUpdate.model_validate(changed), ticket_id)
    with pytest.raises(BizError, match="已启用"):
        await services.save_ticket(WeighingTicketUpdate.model_validate(edit_payload(updated, rateId=encode_id(rate.id))), ticket_id)
    await SettlementRate.filter(id=rate.id).update(enabled=True)
    refreshed = await services.save_ticket(WeighingTicketUpdate.model_validate(edit_payload(updated, rateId=encode_id(rate.id))), ticket_id)
    assert Decimal(refreshed["price"]) == Decimal("9.9999")
    settled = await services.settle_ticket(ticket_id, refreshed["revision"])
    assert settled["isSettled"] is True
    with pytest.raises(BizError, match="已结算"):
        await services.save_ticket(WeighingTicketUpdate.model_validate(edit_payload(settled)), ticket_id)
    with pytest.raises(BizError, match="已结算"):
        await services.delete_tickets([ticket_id])
    # A matched order may be reused in a different ticket.
    data["ticketNo"] = "T-002"
    await services.save_ticket(WeighingTicketCreate.model_validate(data))
    assert await WeighingTicket.all().count() == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_diff_update_removes_and_adds_lines(settlement_db):
    saved = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db)))
    data = edit_payload(saved)
    deleted = decode_id(data["lines"].pop()["id"])
    data["lines"].append(dict(orderId=None, partNo="new", name="新增", netWeight="2.123456", grossWeight="3.123456", quantity=5))
    updated = await services.save_ticket(WeighingTicketUpdate.model_validate(data), decode_id(saved["id"]))
    assert updated["lines"][0]["id"] == saved["lines"][0]["id"]
    assert not await WeighingLine.filter(id=deleted).exists()
    assert len(updated["lines"]) == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_create_and_update_roll_back_on_line_failure(settlement_db, monkeypatch):
    saved = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db)))
    original_create = WeighingLine.create.__func__
    calls = 0

    async def fail_second(cls, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected storage failure")
        return await original_create(cls, **kwargs)

    monkeypatch.setattr(WeighingLine, "create", classmethod(fail_second))
    with pytest.raises(RuntimeError):
        await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db, ticketNo="FAIL")))
    assert await WeighingTicket.all().count() == 1
    assert await WeighingLine.all().count() == 2
    calls = 1
    changed = edit_payload(saved, weight="888.001")
    changed["lines"] = [dict(orderId=None, partNo="new", name="新行", netWeight="1", grossWeight="2", quantity=1)]
    with pytest.raises(RuntimeError):
        await services.save_ticket(WeighingTicketUpdate.model_validate(changed), decode_id(saved["id"]))
    assert await services.detail(decode_id(saved["id"])) == saved


@pytest.mark.asyncio(loop_scope="session")
async def test_http_lookup_validation_and_no_crud_bypass(settlement_db):
    app = FastAPI()
    app.include_router(router)
    register_exceptions(app)
    app.dependency_overrides[PermissionControl.has_permission] = lambda: None
    for number, part in [(1, "AB-partial"), (2, "AB"), (3, "AB")]:
        await Order.create(order_no=f"O-{number}", part_no=part, name="test", net_weight="1.123456")
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        options = await client.get("/settlement_rates/options")
        assert options.json()["data"][0]["processName"] == "喷漆"
        invalid_rate = await client.patch(f'/settlement_rates/{encode_id(settlement_db.id)}', json={'price': '0'})
        assert invalid_rate.json()['code'] != '0000'

        found = (await client.post("/weighing_tickets/order-options", json={"partNo": "AB", "limit": 3})).json()["data"]
        assert len(found) == 3
        assert [row["partNo"] for row in found] == ["AB", "AB", "AB-partial"]
        assert len({row["id"] for row in found}) == 3
        invalid = await client.post("/weighing_tickets", json=payload(settlement_db, totalAmount="1", isSettled=True))
        assert invalid.json()["code"] != "0000"
        created = (await client.post("/weighing_tickets", json=payload(settlement_db))).json()["data"]
        exported = await client.post('/weighing_tickets/export', json={'ids': [created['id']]})
        assert exported.json()['code'] == '0000'
        assert exported.json()['data']['filename'].endswith('.xlsx')
        settled = await client.post(f"/weighing_tickets/{created['id']}/settle", json={"revision": 1})
        assert settled.json()["data"]["isSettled"] is True
        forbidden = await client.patch(f"/weighing_tickets/{created['id']}", json=edit_payload(created))
        assert forbidden.json()["code"] == "4603"
        deleted = await client.delete(f"/weighing_tickets/{created['id']}")
        assert deleted.json()["code"] == "4603"
        bulk = await client.request("DELETE", "/weighing_tickets", json={"ids": [created["id"]]})
        assert bulk.json()["code"] == "4603"
        imported = await client.post("/weighing_tickets/import")
        assert imported.status_code in (404, 405)


@pytest.mark.asyncio(loop_scope="session")
async def test_concurrent_edits_allow_only_one_winner(settlement_db):
    import asyncio

    saved = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db)))
    ticket_id = decode_id(saved['id'])
    results = await asyncio.gather(*[
        services.save_ticket(WeighingTicketUpdate.model_validate(edit_payload(saved, weight=weight)), ticket_id)
        for weight in ('111.001', '222.002')
    ], return_exceptions=True)
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, BizError) for result in results) == 1
    current = await services.detail(ticket_id)
    assert current['revision'] == 2
    assert sum(Decimal(row['allocatedWeight']) for row in current['lines']) == Decimal(current['weight'])


@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_lines_and_foreign_ids_are_rejected(settlement_db):
    from pydantic import ValidationError

    for invalid in [dict(quantity=0), dict(quantity=1.5), dict(quantity=True), dict(netWeight='0'), dict(grossWeight='0'), dict(grossWeight='-1'), dict(grossWeight='1.0000001'), dict(grossWeight='10000000000')]:
        data = payload(settlement_db)
        data['lines'][0].update(invalid)
        with pytest.raises(ValidationError):
            WeighingTicketCreate.model_validate(data)
    data = payload(settlement_db)
    data['lines'][0]['name'] = ' '
    with pytest.raises(BizError):
        await services.save_ticket(WeighingTicketCreate.model_validate(data))
    saved = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db)))
    other = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db, ticketNo='OTHER')))
    changed = edit_payload(saved)
    changed['lines'][0]['id'] = other['lines'][0]['id']
    with pytest.raises(BizError, match='不属于'):
        await services.save_ticket(WeighingTicketUpdate.model_validate(changed), decode_id(saved['id']))
    assert await services.detail(decode_id(saved['id'])) == saved


@pytest.mark.asyncio(loop_scope="session")
async def test_mutations_require_backend_permission(settlement_db):
    app = FastAPI()
    app.include_router(router)
    register_exceptions(app)
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        result = await client.post('/weighing_tickets', json=payload(settlement_db))
        assert result.json()['code'] != '0000'
    assert await WeighingTicket.all().count() == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_decimal_response_uses_fixed_precision_not_exponent_notation(settlement_db):
    data = payload(settlement_db, weight="1000.000")
    data['lines'] = [dict(orderId=None, partNo='P', name='Power of ten', netWeight='0.500000', grossWeight='1.000000', quantity=1000)]
    saved = await services.save_ticket(WeighingTicketCreate.model_validate(data))
    assert saved['weight'] == '1000.000'
    assert saved['price'] == '2.5000'
    assert saved['lines'][0]['theoreticalWeight'] == '1000.000000'
    assert saved['lines'][0]['allocatedWeight'] == '1000.000'
    assert saved['lines'][0]['amount'] == '2500.00'


def test_allocation_uses_gross_weight_times_quantity_not_net_weight():
    amount, lines = calculate(Decimal('100'), Decimal('2'), [
        dict(net_weight=Decimal('9'), gross_weight=Decimal('1'), quantity=2),
        dict(net_weight=Decimal('1'), gross_weight=Decimal('3'), quantity=2),
    ])
    assert [row['theoretical_weight'] for row in lines] == [Decimal('2'), Decimal('6')]
    assert [row['allocated_weight'] for row in lines] == [Decimal('25'), Decimal('75')]
    assert [row['amount'] for row in lines] == [Decimal('50'), Decimal('150')]
    assert amount == Decimal('200')


@pytest.mark.parametrize('gross', [None, Decimal('0'), Decimal('-1')])
def test_allocation_rejects_missing_or_nonpositive_gross_weight(gross):
    with pytest.raises(BizError, match='毛重'):
        calculate(Decimal('100'), Decimal('2'), [dict(net_weight=Decimal('1'), gross_weight=gross, quantity=1)])


@pytest.mark.asyncio(loop_scope='session')
@pytest.mark.parametrize('historical_gross', [None, Decimal('0')])
async def test_missing_historical_gross_weight_can_be_filled_once(settlement_db, historical_gross):
    order = await Order.create(order_no='LEGACY', part_no='P', name='Legacy', net_weight='1', gross_weight='2')
    data = payload(settlement_db)
    data['lines'] = [dict(orderId=encode_id(order.id), quantity=2)]
    saved = await services.save_ticket(WeighingTicketCreate.model_validate(data))
    ticket_id = decode_id(saved['id'])
    await WeighingLine.filter(ticket_id=ticket_id).update(gross_weight=historical_gross)
    with pytest.raises(BizError, match='毛重'):
        await services.settle_ticket(ticket_id, saved['revision'])
    missing = await services.detail(ticket_id)
    blank = edit_payload(missing)
    blank['lines'][0]['grossWeight'] = None
    with pytest.raises(BizError, match='毛重'):
        await services.save_ticket(WeighingTicketUpdate.model_validate(blank), ticket_id)
    edited = edit_payload(missing)
    edited['lines'][0]['grossWeight'] = '3.123456'
    updated = await services.save_ticket(WeighingTicketUpdate.model_validate(edited), ticket_id)
    assert updated['lines'][0]['grossWeight'] == '3.123456'
    assert updated['lines'][0]['theoreticalWeight'] == '6.246912'
    edited = edit_payload(updated)
    edited['lines'][0]['grossWeight'] = '9'
    preserved = await services.save_ticket(WeighingTicketUpdate.model_validate(edited), ticket_id)
    assert preserved['lines'][0]['grossWeight'] == '3.123456'
    settled = await services.settle_ticket(ticket_id, preserved['revision'])
    assert settled['isSettled'] is True


@pytest.fixture
async def ticket_export_client(settlement_db: SettlementRate) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    app.include_router(router)
    register_exceptions(app)
    app.dependency_overrides[PermissionControl.has_permission] = lambda: None
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_export_includes_snapshot_lines_and_ticket_numbers(settlement_db: SettlementRate, ticket_export_client: AsyncClient) -> None:
    order = await Order.create(order_no="000123", part_no="000456-A-01", name="=1+1", net_weight="1.123456", gross_weight="2.654321", quantity=999)
    data = payload(settlement_db)
    data["lines"][1]["partNo"] = "MANUAL002"
    data["lines"].insert(0, dict(orderId=encode_id(order.id), quantity=2))
    first = await services.save_ticket(WeighingTicketCreate.model_validate(data))
    await SettlementRate.filter(id=settlement_db.id).update(process_name="喷砂", price=Decimal("3.7500"))
    data["ticketNo"] = "T-002"
    data["weight"] = "123.456"
    data["lines"] = [dict(orderId=encode_id(order.id), quantity=3)]
    second = await services.save_ticket(WeighingTicketCreate.model_validate(data))
    await Order.filter(id=order.id).update(part_no="NEW-001", name="已修改", gross_weight="99")
    response = await ticket_export_client.post("/weighing_tickets/export", json={"current": 2, "size": 1, "orderBy": ["-id"]})
    assert response.json()["code"] == "0000"
    exported = response.json()["data"]
    assert exported["filename"] == "weighing_tickets.xlsx"
    workbook = load_workbook(BytesIO(b64decode(exported["content"])))
    try:
        assert workbook.sheetnames == ["Data", "订单明细"]
        headers = list(workbook["Data"].values)
        assert [row[0] for row in headers[1:]] == ["T-002", "T-001"]
        assert headers[1][-1] == encode_id(settlement_db.id)
        rows = list(workbook["订单明细"].values)
        assert rows[0] == (
            "磅单编号", "明细顺序", "订单号", "项目号", "名称", "净重", "毛重", "实际过磅数量",
            "机内合重/kg", "分摊过磅重量/kg", "含税结算金额/元", "含税单价（元/件）",
            "磅单总重量/kg", "工序名称", "工序价格（元/kg）", "合同号",
        )
        expected = [(second, line) for line in second["lines"]] + [(first, line) for line in first["lines"]]
        assert len(rows) - 1 == len(expected)
        for row, (ticket, line) in zip(rows[1:], expected, strict=True):
            assert row[:12] == (
                ticket["ticketNo"], line["position"], line["orderNo"], line["partNo"], line["name"],
                line["netWeight"], line["grossWeight"], line["quantity"], line["theoreticalWeight"],
                line["allocatedWeight"], line["amount"], line["taxUnitPrice"],
            )
            assert (Decimal(row[12]), row[13], Decimal(row[14])) == (Decimal(ticket["weight"]), ticket["process"], Decimal(ticket["price"]))
        assert [row[15] for row in rows[1:]] == ["000456", "000456", "manual", "MANUAL002"]
        assert workbook["订单明细"]["E2"].value == "=1+1"
        assert workbook["订单明细"]["E2"].data_type == "s"
        assert rows[1][2:4] == ("000123", "000456-A-01")
        assert rows[-1][2] is None  # Manual entries are exported with their ticket as well.
    finally:
        workbook.close()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("mode", ["selected", "filtered", "intersection", "empty", "empty_ids"])
async def test_ticket_export_applies_same_selection_to_both_sheets(settlement_db: SettlementRate, ticket_export_client: AsyncClient, mode: str) -> None:
    first = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db)))
    second = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db, ticketNo="T-002", weighingDate="2026-11-05")))
    queries = {
        "selected": {"ids": [first["id"]]},
        "filtered": {"weighingDateStart": "2026-11-02", "weighingDateEnd": "2026-11-06", "process": "喷", "isSettled": False, "rateId": encode_id(settlement_db.id)},
        "intersection": {"ids": [first["id"], second["id"]], "ticketNo": "T-002"},
        "empty": {"ids": [first["id"]], "ticketNo": "T-002"},
        "empty_ids": {"ids": []},
    }
    response = await ticket_export_client.post("/weighing_tickets/export", json=queries[mode])
    if mode == "empty_ids":
        assert response.json()["code"] != "0000"
        return
    assert response.json()["code"] == "0000"
    workbook = load_workbook(BytesIO(b64decode(response.json()["data"]["content"])))
    try:
        expected = [] if mode == "empty" else ["T-001" if mode == "selected" else "T-002"]
        assert [row[0] for row in list(workbook["Data"].values)[1:]] == expected
        assert [row[0] for row in list(workbook["订单明细"].values)[1:]] == [number for number in expected for _ in range(2)]
    finally:
        workbook.close()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("main_limit", [True, False])
async def test_ticket_export_rejects_over_limit_without_partial_file(
    settlement_db: SettlementRate, ticket_export_client: AsyncClient, monkeypatch: pytest.MonkeyPatch, main_limit: bool,
) -> None:
    from app.business.weighbridge_settlement import export

    await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db)))
    if main_limit:
        await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db, ticketNo="T-002")))
    monkeypatch.setattr(export, "MAX_EXPORT_ROWS", 1)
    response = await ticket_export_client.post("/weighing_tickets/export", json={})
    result = response.json()
    assert result["code"] != "0000"
    assert "磅单" in result["msg"] if main_limit else "订单明细" in result["msg"]
    assert not result.get("data")


@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_export_still_requires_backend_permission(settlement_db: SettlementRate) -> None:
    app = FastAPI()
    app.include_router(router)
    register_exceptions(app)
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        response = await client.post("/weighing_tickets/export", json={})
    assert response.json()["code"] != "0000"


@pytest.mark.asyncio(loop_scope="session")
async def test_ticket_images_persist_preserve_clear_and_respect_settlement_lock(settlement_db: SettlementRate, ticket_export_client: AsyncClient) -> None:
    images = [f"/system-manage/uploads/content/{number:032x}" for number in range(1, 3)]
    response = await ticket_export_client.post("/weighing_tickets", json=payload(settlement_db, images=images))
    saved = response.json()["data"]
    assert saved["images"] == images
    ticket_id = saved["id"]
    assert (await ticket_export_client.get(f"/weighing_tickets/{ticket_id}")).json()["data"]["images"] == images
    listed = (await ticket_export_client.post("/weighing_tickets/search", json={})).json()
    assert listed["data"]["records"][0]["images"] == images
    # Existing clients that omit the new optional field must not erase attachments.
    unchanged = (await ticket_export_client.patch(f"/weighing_tickets/{ticket_id}", json=edit_payload(saved))).json()["data"]
    assert unchanged["images"] == images
    for value in (list(reversed(images)), [], None):
        unchanged = (await ticket_export_client.patch(f"/weighing_tickets/{ticket_id}", json=edit_payload(unchanged, images=value))).json()["data"]
        assert unchanged["images"] == value
    saved = (await ticket_export_client.patch(f"/weighing_tickets/{ticket_id}", json=edit_payload(unchanged, images=images))).json()["data"]
    await services.settle_ticket(decode_id(ticket_id), saved["revision"])
    denied = await ticket_export_client.patch(f"/weighing_tickets/{ticket_id}", json=edit_payload(saved, images=[]))
    assert denied.json()["code"] == "4603"
    assert (await services.detail(decode_id(ticket_id)))["images"] == images
    legacy = await services.save_ticket(WeighingTicketCreate.model_validate(payload(settlement_db, ticketNo="NO-PHOTO")))
    assert legacy["images"] is None


@pytest.mark.parametrize("images", [
    [f"/system-manage/uploads/content/{number:032x}" for number in range(6)],
    "not-an-array", [""], [123], ["javascript:alert(1)"], ["//example.com/image.jpg"],
    ["/system-manage/uploads/content/../../secret"],
])
def test_ticket_images_validate_count_and_uploaded_paths(images: object) -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        WeighingTicketCreate.model_validate({
            "ticketNo": "T", "weighingDate": "2026-11-06", "weight": "1", "rateId": encode_id(1),
            "lines": [{"partNo": "P", "name": "N", "netWeight": "1", "grossWeight": "1", "quantity": 1}], "images": images,
        })
