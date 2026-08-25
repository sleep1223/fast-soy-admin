from pathlib import Path
from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.autodiscover import discover_business_db_configs, discover_business_models


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "FastSoyAdmin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: list[str] = Field(default_factory=lambda: ["*"])

    APP_DEBUG: bool = False
    RADAR_ENABLED: bool = False

    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    BASE_DIR: Path = PROJECT_ROOT.parent
    LOGS_ROOT: Path = BASE_DIR / "logs/"
    STATIC_ROOT: Path = BASE_DIR / "static/"
    SECRET_KEY: str = "015a42020f023ac2c3eda3d45fe5ca3fef8921ce63589f6d4fcdef9814cd7fa7"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # 数据库连接 URL — Tortoise ORM 原生支持多引擎, 直接在 .env 里覆盖 DB_URL
    # 即可切换, 无需改代码。默认依赖含 PostgreSQL 驱动 (tortoise-orm[asyncpg])
    # 与 SQLite 驱动 (aiosqlite, tortoise-orm 自带); 切到 MySQL / MSSQL / Oracle 需安装
    # 对应 extras: uv sync --extra {mysql|mssql|oracle}。
    # URL 格式参考 tortoise-orm 官方文档:
    #
    #   postgres: postgres://user:password@host:5432/dbname   # 默认走 asyncpg
    #             asyncpg://user:password@host:5432/dbname    # 显式指定 asyncpg
    #             psycopg://user:password@host:5432/dbname    # 显式指定 psycopg
    #
    #   sqlite:   sqlite://DB_FILE                    # 相对路径两个斜杠
    #             sqlite:///data/db.sqlite3           # 绝对路径三个斜杠 (/data/db.sqlite3)
    #             sqlite://app_system.sqlite3?busy_timeout=5000&journal_mode=WAL
    #
    #   mysql:    mysql://user:password@host:3306/dbname
    #
    #   mssql:    mssql://user:password@host:1433/dbname?driver=ODBC%20Driver%2018%20for%20SQL%20Server
    #             # 可追加 &encrypt=no&trust_server_certificate=yes 等 ODBC 选项
    DB_URL: str = "postgres://postgres:password@localhost:5432/fastsoyadmin"

    # Tortoise ORM 配置字典 — 由 DB_URL + autodiscover 在 model_validator 里构建,
    # 无需在 .env 中手动设置 (也不要设置: 多行 JSON 会被 VS Code 等工具的
    # 简易 .env 解析器破坏, 导致环境变量注入失败)。
    TORTOISE_ORM: dict[str, Any] = Field(default_factory=dict)

    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    REDIS_URL: str = "redis://redis:6379/0"  # "redis://:password@233.233.233.233:33333/0"

    # logs - 普通日志保留时间, 支持: seconds/minutes/hours/days/weeks/months/years (如 "30 days", "1 months", "2 weeks")
    LOG_INFO_RETENTION: str = "30 days"

    # 反向代理 — 启用后由 granian.utils.proxies 从 X-Forwarded-For / X-Forwarded-Proto
    # 还原真实客户端 IP 与协议。生产环境部署在 Nginx 之后务必启用。
    # TRUSTED_HOSTS 接受单 IP/CIDR 列表，例如 ["127.0.0.1", "10.0.0.0/8"]；
    # 设为 ["*"] 将信任所有上游（仅在确认无法被外网直连时使用）。
    PROXY_HEADERS_ENABLED: bool = False
    TRUSTED_HOSTS: list[str] = Field(default_factory=lambda: ["127.0.0.1"])

    # fastapi-guard
    GUARD_ENABLED: bool = True
    GUARD_RATE_LIMIT: int = 100
    GUARD_RATE_LIMIT_WINDOW: int = 60
    GUARD_AUTO_BAN_THRESHOLD: int = 10
    GUARD_AUTO_BAN_DURATION: int = 21600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _build_tortoise_orm(self) -> "Settings":
        """从 DB_URL + 业务模块自动发现构建 TORTOISE_ORM 配置。

        已经显式设置 TORTOISE_ORM 的情况下保留不覆盖 (测试夹具会这样用)。
        """
        if self.TORTOISE_ORM:
            return self

        # 业务模块可在 config.py 中声明独立 DB_URL，自动注册为独立连接
        biz_db_configs = discover_business_db_configs()
        # 使用默认连接的模型列表（排除已声明独立连接的模块）
        default_models = ["app.system.models", "app.system.radar.models"]
        for m in discover_business_models():
            module_name = m.split(".")[-2]  # e.g. "app.business.hr.models" -> "hr"
            if module_name not in biz_db_configs:
                default_models.append(m)

        connections: dict[str, str] = {"conn_system": self.DB_URL}
        apps: dict[str, dict] = {
            "app_system": {"models": default_models, "default_connection": "conn_system", "migrations": "migrations.app_system"},
        }

        # 为每个声明了独立 DB_URL 的业务模块注册独立连接和 app
        for biz_name, biz_cfg in biz_db_configs.items():
            if biz_cfg["db_url"] == self.DB_URL:
                # 与系统相同 URL，合并到默认连接
                default_models.append(biz_cfg["models"])
                continue
            conn_name = f"conn_{biz_name}"
            connections[conn_name] = biz_cfg["db_url"]
            apps[f"app_{biz_name}"] = {
                "models": [biz_cfg["models"]],
                "default_connection": conn_name,
                "migrations": f"migrations.app_{biz_name}",
            }

        self.TORTOISE_ORM = {
            "connections": connections,
            "apps": apps,
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }
        return self


APP_SETTINGS = Settings()
TORTOISE_ORM = APP_SETTINGS.TORTOISE_ORM

# 确保必要目录存在
for _dir in [APP_SETTINGS.LOGS_ROOT, APP_SETTINGS.STATIC_ROOT, APP_SETTINGS.BASE_DIR / "migrations"]:
    _dir.mkdir(parents=True, exist_ok=True)
