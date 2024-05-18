from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    ADD_LOG_ORIGINS_INCLUDE: list = ["*"]  # APILoggerMiddleware 和 APILoggerAddResponseMiddleware中间件
    ADD_LOG_ORIGINS_DECLUDE: list = ["/system-manage", "/redoc", "/doc", "/openapi.json"]  # 排除添加API日志的url部分

    DEBUG: bool = True

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    BASE_DIR = PROJECT_ROOT.parent
    LOGS_ROOT = BASE_DIR / "app/logs"
    SECRET_KEY: str = "015a42020f023ac2c3eda3d45fe5ca3fef8921ce63589f6d4fcdef9814cd7fa7"  # python -c "from passlib import pwd; print(pwd.genword(length=64, charset='hex'))"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    TORTOISE_ORM: dict = {
        "connections": {
            # you need to create a database named `fast-soy-admin` in your database before running the project
            # If an error occurs, you can attempt to delete the "migrations/app_system" folder and all tables, and then run the project again

            "conn_system": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {"file_path": f"{BASE_DIR}/db_system.sqlite3"},
            },

            # if you want to use PostgreSQL, you need to install tortoise-orm[asyncpg]
            # "conn_system": {
            #     "engine": "tortoise.backends.asyncpg",
            #     "credentials": {
            #         "host": "localhost",
            #         "port": 5432,
            #         "user": "sleep1223",
            #         "password": "sleep1223",
            #         "database": "fast-soy-admin"
            #     }
            # },

            # if you want to use MySQL/MariaDB, you need to install tortoise-orm[asyncmy]
            # "conn_system": {
            #     "engine": "tortoise.backends.mysql",
            #     "credentials": {
            #         "host": "localhost",
            #         "port": 63306,
            #         "user": "sleep1223",
            #         "password": "sleep1223",
            #         "database": "fast-soy-admin"
            #     }
            # },

            # if you want to use MSSQL/Oracle, you need to install tortoise-orm[asyncodbc]
            # "conn_book": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",
            #         "port": 63306,
            #         "user": "sleep1223",
            #         "password": "sleep1223",
            #         "database": "fast-soy-admin"
            #     }
            # },


        },
        "apps": {
            # don't modify app_system, otherwise you will need to modify all app_systems in app/models/admin.py
            "app_system": {"models": ["app.models.system", "aerich.models"], "default_connection": "conn_system"},
            # "app_book": {"models": ["app.models.book"], "default_connection": "conn_book"},
        },
        "use_tz": False,
        "timezone": "Asia/Shanghai",
    }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"



