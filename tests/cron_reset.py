from app.core.exceptions import SettingNotFound

try:
    from app.settings import APP_SETTINGS
except ImportError:
    raise SettingNotFound("Can not import settings")

from tortoise import Tortoise, run_async


async def init():
    await Tortoise.init(
        config=APP_SETTINGS.TORTOISE_ORM,
    )
    await Tortoise.generate_schemas()

    # 清空所有表
    # await Tortoise._drop_databases()
    # await Tortoise.close_connections()
    conn = Tortoise.get_connection("conn_system")
    print("conn", conn)

    # 获取所有表名
    total, tables = await conn.execute_query('SELECT tablename FROM pg_tables WHERE schemaname = \'public\';')
    # 删除所有表
    for table in tables:
        table_name = table[0]
        print("table_name", table_name)
        if table_name != "aerich":
            await conn.execute_query(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')

    await Tortoise.close_connections()


run_async(init())
