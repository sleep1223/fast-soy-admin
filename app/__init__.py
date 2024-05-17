import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.v1.utils import refresh_api_list
from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_menus,
    init_users,
    make_middlewares,
    modify_db,
    register_db,
    register_exceptions,
    register_routers,
)
from app.models.system import Log
from app.models.system import LogType, LogDetailType

try:
    from app.settings import APP_SETTINGS
except ImportError:
    raise SettingNotFound("Can not import settings")


def create_app() -> FastAPI:
    _app = FastAPI(
        title=APP_SETTINGS.APP_TITLE,
        description=APP_SETTINGS.APP_DESCRIPTION,
        version=APP_SETTINGS.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan
    )
    register_db(_app)
    register_exceptions(_app)
    register_routers(_app, prefix="/api")
    return _app


@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_time = time.time()
    try:
        await modify_db()
        await init_menus()
        await refresh_api_list()
        await init_users()
        await Log.create(log_type=LogType.SystemLog, log_detail_type=LogDetailType.SystemStart)
        yield
    finally:
        end_time = time.time()
        runtime = end_time - start_time
        logger.info(f"App {_app.title} runtime: {runtime} seconds")  # noqa
        await Log.create(log_type=LogType.SystemLog, log_detail_type=LogDetailType.SystemStop)


app = create_app()
