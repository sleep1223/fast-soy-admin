import random

from app.controllers import role_controller, user_controller
from app.core.exceptions import SettingNotFound
from app.models.system import Role, StatusType
from app.schemas.users import UserCreate

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
    role = await role_controller.get_by_code("R_USER")
    if not role:
        raise Exception("Role not found")

    for _ in range(6):
        random_str = "r_" + ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 5))
        random_phone = f"189{random.randint(9999999, 100000000)}"
        role_super: Role | None = await role_controller.get_by_code("R_SUPER")
        user_create = await user_controller.create(
            UserCreate(
                userName=random_str,
                userEmail=f"{random_str}@user.com",
                password="123456",
                user_phone=random_phone,
                status=StatusType.enable
            )
        )
        await user_create.roles.add(role_super)


run_async(init())
