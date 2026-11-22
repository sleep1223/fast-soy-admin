"""月度接收工件的导入和月份规则。"""

from datetime import date

import pytest
from pydantic import ValidationError
from tortoise.context import tortoise_test_context

from app.business.labor_management.models import LaborReceipt
from app.business.labor_management.schemas import LaborReceiptCreate, LaborWorkHourCreate
from app.business.labor_management.services import import_month_receipts
from app.core.excel import write_excel
from app.core.exceptions import BizError
from app.core.sqids import encode_id


@pytest.mark.asyncio(loop_scope="session")
async def test_receipt_import_deduplicates_per_month_and_preserves_unmatched() -> None:
    async with tortoise_test_context(modules=["app.business.labor_management.models"], app_label="app_system", connection_label="conn_system", use_tz=False):
        content = write_excel(["项目号"], [[" P-1 "], ["P-1"], ["UNMATCHED"]])
        assert await import_month_receipts(content, date(2026, 11, 18)) == (2, 1)
        assert await import_month_receipts(content, date(2026, 11, 1)) == (0, 3)
        assert await import_month_receipts(content, date(2026, 12, 1)) == (2, 1)
        assert await LaborReceipt.filter(part_no="UNMATCHED").count() == 2
        assert (await LaborReceipt.get(part_no="P-1", receipt_month=date(2026, 11, 1))).receipt_month.day == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_spreadsheet_does_not_write_rows() -> None:
    async with tortoise_test_context(modules=["app.business.labor_management.models"], app_label="app_system", connection_label="conn_system", use_tz=False):
        content = write_excel(["项目号"], [["VALID"], [" " ]])
        with pytest.raises(BizError):
            await import_month_receipts(content, date(2026, 11, 1))
        assert await LaborReceipt.all().count() == 0


def test_receipt_month_and_ticket_allocation() -> None:
    assert LaborReceiptCreate.model_validate({"receiptMonth": "2026-11-19", "partNo": " P "}).receipt_month == date(2026, 11, 1)
    payload = {"ticketCode": "T", "workHours": 2, "orderNo": "O", "workerId": encode_id(1), "receiptId": encode_id(1)}
    with pytest.raises(ValidationError):
        LaborWorkHourCreate.model_validate(payload)
    assert LaborWorkHourCreate.model_validate({**payload, "allocationMonth": "2026-12-20"}).allocation_month == date(2026, 12, 1)
