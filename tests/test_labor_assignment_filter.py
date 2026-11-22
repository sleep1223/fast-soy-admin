"""工票分配状态在列表与导出中保持一致。"""

from base64 import b64decode
from datetime import date
from io import BytesIO

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openpyxl import load_workbook
from tortoise.context import tortoise_test_context

from app.business.labor_management.controllers import labor_work_hour_controller
from app.business.labor_management.models import LaborWorker, LaborWorkHour
from app.business.labor_management.schemas import LaborWorkHourCreate, LaborWorkHourSearch, LaborWorkHourUpdate
from app.core.sqids import encode_id
from app.utils import CRUDRouter, ExcelConfig, SearchFieldConfig


@pytest.mark.asyncio(loop_scope="session")
async def test_assignment_filter_matches_list_and_export() -> None:
    async with tortoise_test_context(modules=["app.business.labor_management.models"], app_label="app_system", connection_label="conn_system", use_tz=False):
        worker = await LaborWorker.create(employee_no="1", name="A", trade="工种")
        for ticket, month, worker_id in [
            ("both", date(2026, 11, 1), worker.id),
            ("month-only", date(2026, 11, 1), None),
            ("worker-only", None, worker.id),
            ("neither", None, None),
        ]:
            await LaborWorkHour.create(ticket_code=ticket, order_no="O1", work_hours=1, allocation_month=month, worker_id=worker_id)

        crud = CRUDRouter(
            prefix="/tickets", controller=labor_work_hour_controller,
            create_schema=LaborWorkHourCreate, update_schema=LaborWorkHourUpdate, list_schema=LaborWorkHourSearch,
            search_fields=SearchFieldConfig(contains_fields=["order_no"]),
            excel=ExcelConfig(fields=("ticket_code", "work_hours", "order_no", "worker_id", "allocation_month")),
        )
        app = FastAPI()
        app.include_router(crud.router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for assigned, expected in [(True, {"both"}), (False, {"month-only", "worker-only", "neither"}), (None, {"both", "month-only", "worker-only", "neither"})]:
                payload = {"isAssigned": assigned, "orderNo": "O1"}
                result = (await client.post('/tickets/search', json=payload)).json()['data']
                assert {item['ticketCode'] for item in result['records']} == expected
                exported = (await client.post('/tickets/export', json=payload)).json()['data']['content']
                book = load_workbook(BytesIO(b64decode(exported)), read_only=True)
                rows = list(book.active.iter_rows(values_only=True))
                book.close()
                assert {row[0] for row in rows[1:]} == expected

            response = await client.post('/tickets', json={"ticketCode": "new", "orderNo": "O2", "workHours": 2})
            assert response.status_code == 200
            ticket_id = response.json()['data']['createdId']
            before = (await client.post('/tickets/search', json={"isAssigned": False, "orderNo": "O2"})).json()['data']
            assert [item['ticketCode'] for item in before['records']] == ['new']
            response = await client.patch(f'/tickets/{ticket_id}', json={"workerId": encode_id(worker.id), "allocationMonth": "2026-12-01"})
            assert response.status_code == 200
            after = (await client.post('/tickets/search', json={"isAssigned": True, "orderNo": "O2"})).json()['data']
            assert [item['ticketCode'] for item in after['records']] == ['new']
