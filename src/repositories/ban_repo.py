from sqlalchemy import select, delete

from src.repositories.base import BaseRepository
from src.repositories.models import Ban


class BanRepository(BaseRepository):
    async def create(self, tg_id: int) -> Ban:
        ban = Ban(tg_id=tg_id)
        self.session.add(ban)
        await self.session.flush()
        return ban

    async def get(self, ban_id: int) -> Ban | None:
        result = await self.session.execute(
            select(Ban).where(Ban.id == ban_id)
        )
        return result.scalar_one_or_none()

    async def is_banned(self, tg_id: int) -> bool:
        result = await self.session.execute(
            select(Ban).where(Ban.tg_id == tg_id)
        )
        return result.scalar_one_or_none() is not None

    async def is_banned_by_ban_id(self, ban_id: int) -> bool:
        result = await self.session.execute(
            select(Ban).where(Ban.id == ban_id)
        )
        return result.scalar_one_or_none() is not None


    async def unban(self, ban_id: int) -> bool:
        result = await self.session.execute(
            delete(Ban).where(Ban.id == ban_id)
        )
        return result.rowcount > 0