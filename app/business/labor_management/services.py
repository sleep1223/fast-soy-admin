"""劳务管理业务逻辑。"""

from datetime import datetime
from typing import cast

from pydantic import BaseModel, ValidationError
from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction

from app.business.labor_management.controllers import labor_project_controller
from app.business.labor_management.models import LaborProject
from app.business.labor_management.schemas import LaborProjectCreate, LaborProjectUpdate
from app.utils import BizError, Code, get_db_conn


async def import_labor_projects(rows: list[tuple[int, BaseModel]], imported_at: datetime) -> tuple[int, int]:
    """按项目号导入，首次导入时间只写入一次。"""
    created_count = updated_count = 0
    async with in_transaction(get_db_conn(LaborProject)):
        for row_number, raw_item in rows:
            item = cast(LaborProjectCreate, raw_item)
            try:
                existing = await labor_project_controller.get_or_none(part_no=item.part_no)
                if existing is None:
                    values = item.model_dump(exclude_unset=True, exclude_none=True)
                    values["imported_at"] = imported_at
                    await labor_project_controller.create(obj_in=values)
                    created_count += 1
                else:
                    values = LaborProjectUpdate.model_validate(item.model_dump(mode="json", exclude_unset=True, exclude_none=True)).model_dump(exclude_unset=True, exclude_none=True)
                    await labor_project_controller.update(id=existing.id, obj_in=values)
                    await LaborProject.filter(id=existing.id, imported_at__isnull=True).update(imported_at=imported_at)
                    updated_count += 1
            except ValidationError as exc:
                raise BizError(Code.REQUEST_VALIDATION, f"第 {row_number} 行更新字段校验失败，导入已全部回滚") from exc
            except IntegrityError as exc:
                raise BizError(Code.DUPLICATE_RESOURCE, f"第 {row_number} 行违反唯一键或外键约束，导入已全部回滚") from exc
    return created_count, updated_count
