import sys
from typing import Any

from loguru import logger as loguru_logger

from app.settings import APP_SETTINGS

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s - %(name)s - %(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(name)s - %(levelprefix)s  %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
        "access_file": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s - %(name)s - %(levelprefix)s  %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
            "use_colors": False,
        },
    },
    "handlers": {
        "file_handler": {
            "formatter": "access_file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "./app.log",
            "mode": "a+",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 0,
        },
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access", "file_handler"], "level": "INFO", "propagate": False},
    },
}


class Loggin:
    def __init__(self) -> None:
        debug = APP_SETTINGS.DEBUG
        if debug:
            self.level = "DEBUG"
        else:
            self.level = "INFO"

    def setup_logger(self):
        loguru_logger.remove()
        loguru_logger.add(sink=sys.stdout, level=self.level)
        loguru_logger.add("my_project.log", level=self.level, rotation="100 MB")  # Output log messages to a file
        return loguru_logger


loggin = Loggin()
logger = loggin.setup_logger()
