from loguru import logger

from app.core.crud import CRUDBase
from app.models.system import Button, Menu
from app.schemas.menus import ButtonBase, MenuCreate, MenuUpdate


class MenuController(CRUDBase[Menu, MenuCreate, MenuUpdate]):
    def __init__(self):
        super().__init__(model=Menu)

    # async def get_by_menu_name(self, menu_name: str) -> Menu | None:
    #     return await self.model.filter(menu_name=menu_name).first()
    #
    # async def get_by_route_path(self, route_path: str) -> Menu | None:
    #     return await self.model.filter(route_path=route_path).first()

    @staticmethod
    async def update_buttons_by_code(menu: Menu, buttons: list[ButtonBase] | None = None) -> bool:
        if not buttons:
            return False

        existing_buttons = [button.button_code for button in await menu.buttons]

        menu_buttons = [button.button_code for button in buttons]

        for button_code in set(existing_buttons) - set(menu_buttons):
            logger.error(f"Button Deleted {button_code}")
            await Button.filter(button_code=button_code).delete()

        await menu.buttons.clear()
        for button in buttons:
            button_obj, _ = await Button.update_or_create(button_code=button.button_code, defaults=dict(button_desc=button.button_desc))
            await menu.buttons.add(button_obj)

        return True


menu_controller = MenuController()
