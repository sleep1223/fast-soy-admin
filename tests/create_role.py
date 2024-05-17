import random

from app.core.exceptions import SettingNotFound
from app.models.system import Menu, Role

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
    await add_user()


async def add_user():
    menu_objs = await Menu.filter(constant=False)

    for _ in range(6):
        random_str = "u_" + ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5))
        role_admin = await Role.create(role_name=random_str, role_code=random_str, role_desc="test")
        for menu_obj in menu_objs:
            await role_admin.menus.add(menu_obj)


run_async(init())
