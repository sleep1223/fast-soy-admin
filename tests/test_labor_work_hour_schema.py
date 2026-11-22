"""劳务工票的人员分配校验。"""

from datetime import date

from app.business.labor_management.schemas import LaborWorkHourCreate, LaborWorkHourUpdate
from app.core.sqids import encode_id


def test_new_work_hour_may_be_unassigned() -> None:
    data = {"ticketCode": "T001", "orderNo": "O001", "workHours": "2.50"}
    assert LaborWorkHourCreate.model_validate(data).worker_id is None
    assert LaborWorkHourCreate.model_validate({**data, "workerId": None}).worker_id is None
    assert LaborWorkHourCreate.model_validate({**data, "workerId": encode_id(1)}).worker_id == 1


def test_legacy_work_hour_can_be_updated_without_worker() -> None:
    assert LaborWorkHourUpdate.model_validate({"ticketCode": "T001"}).model_dump(exclude_unset=True) == {"ticket_code": "T001"}


def test_allocation_month_is_normalized() -> None:
    assert LaborWorkHourUpdate.model_validate({"allocationMonth": "2026-12-20"}).allocation_month == date(2026, 12, 1)
