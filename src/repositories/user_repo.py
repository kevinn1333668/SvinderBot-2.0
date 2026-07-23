from sqlalchemy import select, delete

from src.repositories.base import BaseRepository
from src.repositories.models import User


class UserRepository(BaseRepository):
    async def get_by_tg_id(self, tg_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def exists_by_tg_id(self, tg_id: int) -> bool:
        user  = await self.get_by_tg_id(tg_id)
        return user is not None

    async def create(self, tg_id: int, username: str | None = None) -> User:
        user = User(tg_id=tg_id, username=username)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_all(self) -> list[int]:
        result = await self.session.execute(select(User.tg_id))
        tg_ids = [row[0] for row in result]
        return tg_ids