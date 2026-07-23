from sqlalchemy.exc import IntegrityError

from src.repositories.models import User
from src.repositories.uow import UnitOfWork


class UserService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def register_if_new(self, tg_id: int, username: str | None = None) -> bool:
        async with self._uow as uow:
            if await uow.users.exists_by_tg_id(tg_id):
                return False

            try:
                await uow.users.create(tg_id, username)
                await uow.commit()
                return True
            except IntegrityError:
                await uow.rollback()
                return False

    async def get_user_by_tg_id(self, tg_id: int) -> User | None:
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(tg_id)

            return user

    async def get_user_by_username(self, username: str) -> User | None:
        async with self._uow as uow:
            user = await uow.users.get_by_username(username)

            return user

    async def get_all_tg_ids(self) -> list[int]:
        async with self._uow as uow:
            tg_ids = await uow.users.get_all()
            return tg_ids
