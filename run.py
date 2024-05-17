import uvicorn

from app.log.log import LOGGING_CONFIG

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9999, reload=False, log_config=LOGGING_CONFIG)
