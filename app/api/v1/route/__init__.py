from fastapi import APIRouter

from .route import router

router_route = APIRouter()
router_route.include_router(router)
