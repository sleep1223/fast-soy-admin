"""Export ticket headers and their saved order snapshots in one bounded workbook."""

from asyncio import to_thread
from collections import defaultdict
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.business.weighbridge_settlement.models import WeighingLine, WeighingTicket
from app.business.weighbridge_settlement.schemas import MAX_EXPORT_ROWS, WeighingTicketOut
from app.utils import BizError, Code, ExcelConfig, get_db_conn

TICKET_EXCEL = ExcelConfig(fields=("ticket_no", "weighing_date", "weight", "process", "price", "total_amount", "is_settled", "revision", "rate_id"))
LINE_COLUMNS = (
    ("position", "明细顺序"),
    ("order_no", "订单号"),
    ("part_no", "项目号"),
    ("name", "名称"),
    ("net_weight", "净重"),
    ("gross_weight", "毛重"),
    ("quantity", "实际过磅数量"),
    ("theoretical_weight", "机内合重/kg"),
    ("allocated_weight", "分摊过磅重量/kg"),
    ("amount", "含税结算金额/元"),
    ("tax_unit_price", "含税单价（元/件）"),
)
DETAIL_TICKET_COLUMNS = (
    ("weight", "磅单总重量/kg"),
    ("process", "工序名称"),
    ("price", "工序价格（元/kg）"),
)


def _write_workbook(ticket_rows: list[list[Any]], line_rows: list[list[Any]]) -> bytes:
    headers, _ = TICKET_EXCEL.resolve(WeighingTicketOut)
    detail_headers = ["磅单编号", *[title for _, title in LINE_COLUMNS + DETAIL_TICKET_COLUMNS], "合同号"]
    workbook = Workbook(write_only=True)
    try:
        # Preserve the existing main sheet and append the matching detail sheet.
        for title, rows in (
            ("Data", [headers, *ticket_rows]),
            ("订单明细", [detail_headers, *line_rows]),
        ):
            sheet = workbook.create_sheet(title)
            for row in rows:
                cells = []
                for value in row:
                    if isinstance(value, Decimal):
                        value = format(value, "f")
                    elif isinstance(value, date):
                        value = value.isoformat()
                    if isinstance(value, str) and (len(value) > 32767 or ILLEGAL_CHARACTERS_RE.search(value)):
                        raise BizError(Code.REQUEST_VALIDATION, "数据超过 Excel 单元格长度限制或包含不支持的字符")
                    cell = WriteOnlyCell(sheet, value=value)
                    # Identifiers and formula-looking user input must remain literal text.
                    if isinstance(value, str):
                        cell.data_type = "s"
                    cells.append(cell)
                sheet.append(cells)
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()
    finally:
        workbook.close()


async def export_tickets(search: Q, order: list[str]) -> bytes:
    async with in_transaction(get_db_conn(WeighingTicket)) as db:
        # Lock in the same ID order as bulk deletion, independently of display sorting.
        tickets = await WeighingTicket.filter(search).using_db(db).order_by("id").limit(MAX_EXPORT_ROWS + 1).select_for_update()
        if len(tickets) > MAX_EXPORT_ROWS:
            raise BizError(Code.REQUEST_VALIDATION, f"导出最多 {MAX_EXPORT_ROWS} 行磅单，请缩小筛选范围")
        if tickets and order != ["id"]:
            tickets = await WeighingTicket.filter(id__in=[ticket.id for ticket in tickets]).using_db(db).order_by(*order)
        lines = await WeighingLine.filter(ticket_id__in=[ticket.id for ticket in tickets]).using_db(db).order_by("ticket_id", "position").limit(MAX_EXPORT_ROWS + 1)
        if len(lines) > MAX_EXPORT_ROWS:
            raise BizError(Code.REQUEST_VALIDATION, f"订单明细导出最多 {MAX_EXPORT_ROWS} 行，请缩小筛选范围")
        grouped: dict[int, list[WeighingLine]] = defaultdict(list)
        for line in lines:
            grouped[line.ticket_id].append(line)
        ticket_rows: list[list[Any]] = []
        line_rows: list[list[Any]] = []
        for ticket in tickets:
            # Keep the existing schema serialization, including the Sqid rate ID.
            values = {name: getattr(ticket, name) for name in TICKET_EXCEL.fields}
            record = WeighingTicketOut.model_construct(**values).model_dump(mode="json", include=set(TICKET_EXCEL.fields))
            ticket_rows.append([record[name] for name in TICKET_EXCEL.fields])
            detail_ticket_values = [record[name] for name, _ in DETAIL_TICKET_COLUMNS]
            for line in grouped[ticket.id]:
                row: list[Any] = [ticket.ticket_no]
                for name, _ in LINE_COLUMNS:
                    value = getattr(line, name)
                    if isinstance(value, Decimal):
                        places = getattr(WeighingLine._meta.fields_map[name], "decimal_places")
                        value = format(value, f".{places}f")
                    row.append(value)
                contract_no = line.part_no.partition("-")[0]
                line_rows.append([*row, *detail_ticket_values, contract_no])
    # XLSX compression must not block the event loop or hold database locks.
    return await to_thread(_write_workbook, ticket_rows, line_rows)
