from pydantic_settings import BaseSettings

from app.core.config import APP_SETTINGS


class RadarSettings(BaseSettings):
    RADAR_ENABLED: bool = APP_SETTINGS.RADAR_ENABLED
    RADAR_RETENTION_HOURS: int = 24
    RADAR_MAX_BODY_SIZE: int = 65536
    RADAR_EXCLUDE_PATHS: list[str] = [
        "/__radar",
        "/health",
        "/static",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/doc",
        "/api/v1/auth/",
        "/api/v1/monitor/",
        "/api/v1/route/constant-routes",
        "/api/v1/route/user-routes",
        "/api/v1/auth/user-info",
    ]
    RADAR_INCLUDE_PATHS: list[str] = [
        "/__radar/api/_boom",
    ]
    RADAR_SLOW_QUERY_THRESHOLD_MS: float = 100.0
    RADAR_CAPTURE_RESPONSE_BODY: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


RADAR_SETTINGS = RadarSettings()
