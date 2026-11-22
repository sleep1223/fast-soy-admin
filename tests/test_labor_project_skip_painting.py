"""劳务项目的无需刷漆标记。"""

import pytest
from base64 import b64decode
from io import BytesIO
from datetime import datetime, timezone
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openpyxl import load_workbook
from tortoise.context import tortoise_test_context

from app.business.labor_management.api.manage import import_projects, labor_project_crud
from app.business.labor_management.controllers import labor_project_controller
from app.business.labor_management.models import LaborProject
from app.business.labor_management.schemas import LaborProjectCreate, LaborProjectSearch, LaborProjectUpdate
from app.core.excel import write_excel
from app.core.sqids import encode_id
from app.utils import CRUDRouter


@pytest.mark.asyncio(loop_scope="session")
async def test_skip_painting_defaults_can_be_updated_and_survives_legacy_import() -> None:
    async with tortoise_test_context(modules=["app.business.labor_management.models"], app_label="app_system", connection_label="conn_system", use_tz=False):
        existing = await LaborProject.create(part_no="P1", skip_painting=True)
        crud = CRUDRouter(
            prefix="/projects", controller=labor_project_controller,
            create_schema=LaborProjectCreate, update_schema=LaborProjectUpdate, list_schema=LaborProjectSearch,
            excel=labor_project_crud.excel,
            search_fields=labor_project_crud.search_fields,
        )
        app = FastAPI()
        app.include_router(crud.router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            content = write_excel(["项目号"], [["P1"], ["P2"]])
            response = await client.post('/projects/import', files={"file": ("projects.xlsx", content)})
            assert response.status_code == 200
            assert response.json()['data']['createdCount'] == 1
            await existing.refresh_from_db()
            assert existing.skip_painting is True
            created = await LaborProject.get(part_no="P2")
            assert created.skip_painting is False
            for selected, expected in [(False, {"P2"}), (True, {"P1"}), (None, {"P1", "P2"})]:
                payload = {"skipPainting": selected}
                result = (await client.post('/projects/search', json=payload)).json()['data']
                assert {item['partNo'] for item in result['records']} == expected
                exported = (await client.post('/projects/export', json=payload)).json()['data']['content']
                book = load_workbook(BytesIO(b64decode(exported)), read_only=True)
                rows = list(book.active.iter_rows(values_only=True))
                book.close()
                assert {row[0] for row in rows[1:]} == expected


@pytest.mark.asyncio(loop_scope="session")
async def test_first_import_time_is_preserved_and_filter_applies_to_export() -> None:
    async with tortoise_test_context(modules=["app.business.labor_management.models"], app_label="app_system", connection_label="conn_system", use_tz=True, timezone="Asia/Shanghai"):
        manual = await LaborProject.create(part_no="MANUAL", skip_painting=True)
        already = await LaborProject.create(part_no="EARLIER", imported_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
        crud = CRUDRouter(
            prefix="/projects", controller=labor_project_controller,
            create_schema=LaborProjectCreate, update_schema=LaborProjectUpdate, list_schema=LaborProjectSearch,
            excel=labor_project_crud.excel, search_fields=labor_project_crud.search_fields,
        )
        app = FastAPI()
        app.post('/import')(import_projects)
        app.include_router(crud.router)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            content = write_excel(["项目号"], [["MANUAL"], ["EARLIER"], ["NEW"]])
            first = await client.post('/import', files={"file": ("projects.xlsx", content)})
            assert first.json()['data'] == {"importedCount": 3, "createdCount": 1, "updatedCount": 2}
            await manual.refresh_from_db()
            first_time = manual.imported_at
            assert first_time is not None
            assert manual.skip_painting is True
            await already.refresh_from_db()
            assert already.imported_at == datetime(2025, 1, 1, tzinfo=timezone.utc)
            second = await client.post('/import', files={"file": ("projects.xlsx", content)})
            assert second.json()['data']['updatedCount'] == 3
            await manual.refresh_from_db()
            assert manual.imported_at == first_time
            result = (await client.post('/projects/search', json={"importedAtStart": "2024-01-01T00:00:00Z", "importedAtEnd": "2025-12-31T23:59:59Z"})).json()['data']
            assert {item['partNo'] for item in result['records']} == {"EARLIER"}
            local_range = (await client.post('/projects/search', json={"importedAtStart": "2025-01-01T07:59:00+08:00", "importedAtEnd": "2025-01-01T08:01:00+08:00"})).json()['data']
            assert {item['partNo'] for item in local_range['records']} == {"EARLIER"}
            exported = (await client.post('/projects/export', json={"importedAtStart": "2024-01-01T00:00:00Z", "importedAtEnd": "2025-12-31T23:59:59Z"})).json()['data']['content']
            book = load_workbook(BytesIO(b64decode(exported)), read_only=True)
            assert {row[0] for row in list(book.active.iter_rows(values_only=True))[1:]} == {"EARLIER"}
            book.close()
            edited_time = datetime(2024, 6, 1, 12, 30, tzinfo=timezone.utc)
            edited = await client.patch(f'/projects/{encode_id(manual.id)}', json={"importedAt": edited_time.isoformat()})
            assert edited.status_code == 200
            await manual.refresh_from_db()
            assert manual.imported_at == edited_time
            assert manual.skip_painting is True
            await client.post('/import', files={"file": ("projects.xlsx", content)})
            await manual.refresh_from_db()
            assert manual.imported_at == edited_time
