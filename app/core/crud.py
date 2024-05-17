from typing import Any, Generic, NewType, TypeVar

from pydantic import BaseModel
from pydantic.main import IncEx
from tortoise.expressions import Q
from tortoise.models import Model

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, id: int) -> ModelType:
        return await self.model.get(id=id)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list[str] | None = None) -> tuple[Total, list[ModelType]]:
        if order is None:
            order = []

        query = self.model.filter(search)
        total = await query.count()
        result = await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)
        return Total(total), result

    async def create(self, obj_in: CreateSchemaType, exclude: IncEx = None) -> ModelType:
        if isinstance(obj_in, dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude_none=True, exclude=exclude)
        obj: ModelType = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(self, id: int, obj_in: UpdateSchemaType | dict[str, Any], exclude: IncEx = None) -> ModelType:
        if isinstance(obj_in, dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude_none=True,  exclude=exclude)
        obj = await self.get(id=id)
        obj = obj.update_from_dict(obj_dict)

        await obj.save()
        return obj

    async def remove(self, id: int) -> None:
        obj = await self.get(id=id)
        await obj.delete()
