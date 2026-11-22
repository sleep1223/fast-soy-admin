"""项目和工票批量精确匹配使用原有查询权限与分页。"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from tortoise.context import tortoise_test_context

from app.business.labor_management.api.manage import labor_work_hour_crud
from app.business.labor_management.models import LaborWorkHour
from app.business.order_management.api.manage import order_crud
from app.business.order_management.models import Order


@pytest.mark.asyncio(loop_scope="session")
async def test_batch_filters_are_exact_and_existing_fuzzy_search_is_unchanged() -> None:
    async with tortoise_test_context(modules=["app.business.order_management.models", "app.business.labor_management.models"], app_label="app_system", connection_label="conn_system", use_tz=False):
        await Order.create(order_no="O1", part_no="P1", name="A")
        await Order.create(order_no="O10", part_no="P10", name="B")
        await Order.create(order_no="O2", part_no="P2", name="C")
        await LaborWorkHour.create(ticket_code="T1", order_no="O1", work_hours=1)
        await LaborWorkHour.create(ticket_code="T10", order_no="O10", work_hours=1)
        app = FastAPI()
        app.include_router(order_crud.router)
        app.include_router(labor_work_hour_crud.router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post('/orders/search', json={"partNos": ["P1", "P2"], "size": 1})
            assert response.status_code == 200
            assert response.json()['data']['total'] == 2
            fuzzy = (await client.post('/orders/search', json={"partNo": "P1"})).json()['data']
            assert {row['partNo'] for row in fuzzy['records']} == {"P1", "P10"}
            no_matches = (await client.post('/orders/search', json={"partNos": []})).json()['data']
            assert no_matches['total'] == 0
            tickets = (await client.post('/labor_work_hours/search', json={"orderNos": ["O1"]})).json()['data']
            assert [row['ticketCode'] for row in tickets['records']] == ["T1"]
            too_many = await client.post('/orders/search', json={"partNos": [f"P{i}" for i in range(101)]})
            assert too_many.status_code == 422
