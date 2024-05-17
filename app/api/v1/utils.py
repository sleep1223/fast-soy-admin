from fastapi.routing import APIRoute
from loguru import logger

from app.core.ctx import CTX_USER_ID
from app.models.system import Api, Log
from app.models.system import LogType, LogDetailType


async def refresh_api_list():
    from app import app

    existing_apis = [(str(api.method.value), api.path) for api in await Api.all()]

    app_routes = [route for route in app.routes if isinstance(route, APIRoute)]
    app_routes_compared = [(list(route.methods)[0].lower(), route.path_format) for route in app_routes]

    for method, path in set(existing_apis) - set(app_routes_compared):
        logger.error(f"API Deleted {method} {path}")
        await Api.filter(method=method, path=path).delete()

    for route in app_routes:
        method = list(route.methods)[0].lower()
        path = route.path_format
        summary = route.summary
        tags = list(route.tags)
        await Api.update_or_create(path=path, method=method, defaults=dict(summary=summary, tags=tags))
        # api_obj = await Api.get_or_none(path=path, method=method)
        # if api_obj:
        #     await api_obj.update_from_dict(dict(path=path, method=method, summary=summary, tags=tags))
        # else:
        #     await Api.create(path=path, method=method, summary=summary, tags=tags)


async def insert_log(log_type: LogType, log_detail_type: LogDetailType, by_user_id: int | None = None):
    """
    插入日志
    :param log_type:
    :param log_detail_type:
    :param by_user_id: 0为从上下文获取当前用户id, 需要请求携带token
    :return:
    """
    if by_user_id == 0 and (by_user_id := CTX_USER_ID.get()) == 0:
        by_user_id = None

    await Log.create(log_type=log_type, log_detail_type=log_detail_type, by_user_id=by_user_id)
