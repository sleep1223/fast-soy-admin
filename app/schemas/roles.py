from typing import Annotated

from pydantic import BaseModel, Field

from app.models.system import StatusType


class RoleBase(BaseModel):
    role_name: str = Field(alias="roleName", description="角色名称")
    role_code: str = Field(alias="roleCode", description="角色编码")
    role_desc: Annotated[str | None, Field(alias="roleDesc", description="角色描述")] = None
    role_home: Annotated[str | None, Field(alias="roleHome", description="角色首页")] = None
    status: Annotated[StatusType | None, Field()] = None

    class Config:
        populate_by_name = True


class RoleCreate(RoleBase):
    ...


class RoleUpdate(RoleBase):
    ...


class RoleUpdateAuthrization(BaseModel):
    role_home: Annotated[str | None, Field(alias="roleHome", description="角色首页")] = None
    menu_ids: Annotated[list[int] | None, Field(alias="menuIds", description="菜单id列表")] = None
    api_ids: Annotated[list[int] | None, Field(alias="apiIds", description="API id列表")] = None
    button_ids: Annotated[list[int] | None, Field(alias="buttonIds", description="按钮id列表")] = None
