from __future__ import annotations

from fastapi import FastAPI

from app.system.radar.config import RADAR_SETTINGS
from app.system.radar.query_capture import install_query_capture, uninstall_query_capture


def setup_radar(app: FastAPI) -> None:
    """挂载 Radar 路由到 FastAPI 应用，未启用时跳过。"""
    if not RADAR_SETTINGS.RADAR_ENABLED:
        return

    # 延迟导入，避免 app.core.dependency 初始化期间经 radar 包形成循环依赖。
    from app.system.radar.api import router as radar_router

    app.include_router(radar_router)


async def startup_radar() -> None:
    """应用启动时安装 SQL 查询捕获补丁，未启用时跳过。"""
    if not RADAR_SETTINGS.RADAR_ENABLED:
        return

    install_query_capture()


async def shutdown_radar() -> None:
    """应用关闭时卸载 SQL 查询捕获补丁，未启用时跳过。"""
    if not RADAR_SETTINGS.RADAR_ENABLED:
        return

    uninstall_query_capture()
