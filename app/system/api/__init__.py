from fastapi import APIRouter

from app.core.dependency import DependPermission

from .apis import router as api_router
from .auth import router as auth_router
from .dictionary import router as dictionary_router
from .menus import router as menu_router
from .ocr import router as ocr_router
from .roles import router as role_router
from .route import router as route_router
from .upload import router as upload_router
from .users import router as user_router

system_router = APIRouter()
system_router.include_router(upload_router, prefix="/system-manage", tags=["图片上传"])

system_router.include_router(auth_router, prefix="/auth", tags=["权限认证"])
system_router.include_router(route_router, prefix="/route", tags=["路由管理"])
system_router.include_router(api_router, prefix="/system-manage", tags=["API管理"], dependencies=[DependPermission])
system_router.include_router(dictionary_router, prefix="/system-manage", tags=["字典管理"], dependencies=[DependPermission])
system_router.include_router(menu_router, prefix="/system-manage", tags=["菜单管理"], dependencies=[DependPermission])
system_router.include_router(ocr_router, prefix="/system-manage", tags=["OCR"], dependencies=[DependPermission])
system_router.include_router(role_router, prefix="/system-manage", tags=["角色管理"], dependencies=[DependPermission])
system_router.include_router(user_router, prefix="/system-manage", tags=["用户管理"], dependencies=[DependPermission])
