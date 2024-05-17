from fastapi import APIRouter

from .auth import router

router_auth = APIRouter()
router_auth.include_router(router)
