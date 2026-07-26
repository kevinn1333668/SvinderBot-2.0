from datetime import timezone, datetime, timedelta

from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert

from src.repositories.base import BaseRepository
from src.repositories.models import Dislike


class DislikeRepository(BaseRepository):
    async def create(self, disliker_tg_id: int, disliked_tg_id: int, cooldown_minutes: int) -> bool:
        until = datetime.now(timezone.utc) + timedelta(minutes=cooldown_minutes)

        stmt = insert(Dislike).values(
            disliker_tg_id=disliker_tg_id,
            disliked_tg_id=disliked_tg_id,
            until=until,
        ).on_conflict_do_update(
            index_elements=("disliker_tg_id", "disliked_tg_id"),
            set_={"until": until},
        )
        await self.session.execute(stmt)
        return True

    async def delete_expired(self) -> int:
        result = await self.session.execute(
            delete(Dislike).where(Dislike.until <= func.now())
        )
        return result.rowcount