from sqlalchemy import select, delete

from src.repositories.base import BaseRepository
from src.repositories.models import Like


class LikeRepository(BaseRepository):
    async def create(self, liker_tg_id: int, liked_tg_id: int) -> Like:
        like = Like(liker_tg_id=liker_tg_id, liked_tg_id=liked_tg_id)
        self.session.add(like)
        await self.session.flush()
        return like

    async def get_mutual(self, liker_tg_id: int, liked_tg_id: int) -> Like | None:
        stmt = select(Like).where(
            Like.liker_tg_id == liked_tg_id,
            Like.liked_tg_id == liker_tg_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_pair(self, liker_tg_id: int, liked_tg_id: int) -> Like | None:
        stmt = select(Like).where(
            Like.liker_tg_id == liker_tg_id,
            Like.liked_tg_id == liked_tg_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def accept(self, liker_tg_id: int, liked_tg_id: int) -> bool:
        like = await self.get_by_pair(liker_tg_id, liked_tg_id)

        if like is None:
            return False
        like.is_accepted = True
        await self.session.flush()
        return True

    async def delete(self, liker_tg_id: int, liked_tg_id: int) -> bool:
        stmt = (
            delete(Like)
            .where(
                Like.liker_tg_id == liker_tg_id,
                Like.liked_tg_id == liked_tg_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def is_exists(self, liker_tg_id: int, liked_tg_id: int) -> bool:
        return await self.get_by_pair(liker_tg_id, liked_tg_id) is not None