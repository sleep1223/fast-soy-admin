from datetime import datetime

from app.core.crud import CRUDBase
from app.core.exceptions import HTTPException
from app.models.system import Role, User, Log, StatusType
from app.models.system import LogType, LogDetailType
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.utils.security import get_password_hash, verify_password


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, user_email: str) -> User | None:
        return await self.model.filter(user_email=user_email).first()

    async def get_by_username(self, user_name: str) -> User | None:
        return await self.model.filter(user_name=user_name).first()

    async def create(self, obj_in: UserCreate) -> User:  # type: ignore
        obj_in.password = get_password_hash(password=obj_in.password)
        if not obj_in.nick_name:
            obj_in.nick_name = obj_in.user_name
        obj = await super().create(obj_in, exclude={"roles"})
        return obj

    async def update(self, user_id: int, obj_in: UserUpdate) -> User:  # type: ignore
        if obj_in.password:
            obj_in.password = get_password_hash(password=obj_in.password)
        else:
            obj_in.password = None
        return await super().update(id=user_id, obj_in=obj_in, exclude={"roles"})

    async def update_last_login(self, user_id: int) -> None:
        user = await self.model.get(id=user_id)
        user.last_login = datetime.now()
        await user.save()

    async def authenticate(self, credentials: CredentialsSchema) -> User:
        user = await self.model.filter(user_name=credentials.user_name).first()
        if not user:
            await Log.create(log_type=LogType.UserLog, by_user=None, log_detail_type=LogDetailType.UserLoginUserNameVaild)
            raise HTTPException(code="4040", msg="Incorrect username or password!")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            await Log.create(log_type=LogType.UserLog, by_user=None, log_detail_type=LogDetailType.UserLoginErrorPassword)
            raise HTTPException(code="4040", msg="Incorrect username or password!")
        if user.status == StatusType.disable:
            await Log.create(log_type=LogType.UserLog, by_user=None, log_detail_type=LogDetailType.UserLoginForbid)
            raise HTTPException(code="4030", msg="This user has been disabled.")
        return user

    @staticmethod
    async def update_roles(user: User, role_ids: list[int] | None = None) -> bool:
        if not role_ids:
            return False

        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await Role.get(id=role_id)
            await user.roles.add(role_obj)
        return True

    @staticmethod
    async def update_roles_by_code(user: User, roles_codes: list[str] | None = None) -> bool:
        if not roles_codes:
            return False

        await user.roles.clear()
        for role_code in roles_codes:
            role_obj = await Role.get(role_code=role_code)
            await user.roles.add(role_obj)
        return True


user_controller = UserController()
