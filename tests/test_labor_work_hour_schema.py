"""劳务工票的人员分配校验。"""

import pytest
from pydantic import ValidationError

from app.business.labor_management.schemas import LaborWorkHourCreate, LaborWorkHourUpdate
from app.core.sqids import encode_id


def test_new_work_hour_requires_worker() -> None:
    data = {"ticketCode": "T001", "orderNo": "O001", "workHours": "2.50"}
    with pytest.raises(ValidationError):
        LaborWorkHourCreate.model_validate(data)
    assert LaborWorkHourCreate.model_validate({**data, "workerId": encode_id(1)}).worker_id == 1


def test_legacy_work_hour_can_be_updated_without_worker() -> None:
    assert LaborWorkHourUpdate.model_validate({"ticketCode": "T001"}).model_dump(exclude_unset=True) == {"ticket_code": "T001"}
