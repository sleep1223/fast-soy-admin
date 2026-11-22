"""
labor_management services — 业务逻辑层。
"""

from datetime import date
from typing import cast

from tortoise.transactions import in_transaction

from app.business.labor_management.models import LaborReceipt
from app.business.labor_management.schemas import LaborReceiptImportRow
from app.utils import BizError, Code, ExcelConfig, get_current_user, get_db_conn, parse_excel


async def import_month_receipts(content: bytes, receipt_month: date) -> tuple[int, int]:
    """校验整张表后，在一个事务中按月份和项目号追加。"""
    result = parse_excel(content, LaborReceiptImportRow, ExcelConfig(fields=("part_no",)))
    if result.preview.errors:
        raise BizError(Code.REQUEST_VALIDATION, result.preview.errors[0])
    user = get_current_user()
    username = str(user.user_name) if user and user.user_name else None
    month = receipt_month.replace(day=1)
    created = 0
    async with in_transaction(get_db_conn(LaborReceipt)) as connection:
        for _, item in result.rows:
            _, is_new = await LaborReceipt.get_or_create(receipt_month=month, part_no=cast(LaborReceiptImportRow, item).part_no, defaults={"created_by": username}, using_db=connection)
            created += int(is_new)
    return created, len(result.rows) - created
