import logging
from typing import Optional

from sqlalchemy.exc import IntegrityError

from src.repositories.uow import UnitOfWork
from src.schemas.like import LikeDTO

logger = logging.getLogger(__name__)

class LikeService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def is_like_exist(self, liker_tg_id: int, liked_tg_id: int) -> bool:
        async with self._uow as uow:
            return await uow.likes.is_exists(liker_tg_id, liked_tg_id)

    async def like_profile(self, liker_tg_id: int, liked_tg_id: int) -> Optional[LikeDTO]:
        async with self._uow as uow:
            try:
                logger.info("Creating: (tg_id=%s) to (tg_id=%s)", liker_tg_id, liked_tg_id)
                await uow.likes.create(liker_tg_id=liker_tg_id, liked_tg_id=liked_tg_id)
            except IntegrityError:
                logger.exception(
                    "Like user (tg_id=%s) already exists in profile (tg_id=%s)",
                    liker_tg_id, liked_tg_id
                )
                await uow.rollback()
                return None
            mutual = await uow.likes.get_mutual(liker_tg_id, liked_tg_id)

            if mutual:
                await uow.likes.accept(liker_tg_id, liked_tg_id)
                await uow.likes.accept(liked_tg_id, liker_tg_id)

            liked_profile = await uow.profiles.get_profile_by_tg_id(liked_tg_id)
            liker_profile = await uow.profiles.get_profile_by_tg_id(liker_tg_id)

            await uow.commit()

            return LikeDTO(
                liker_profile=liker_profile,
                liked_profile=liked_profile,
                is_match=bool(mutual)
            )

    async def reject_like(self, liker_tg_id: int, liked_tg_id: int) -> bool:
        async with self._uow as uow:
            if await uow.likes.is_exists(liker_tg_id, liked_tg_id):
                result = await uow.likes.delete(liker_tg_id, liked_tg_id)
                await uow.commit()
                return result
            return False


    async def accept_mutual(self, liker_tg_id, liked_tg_id) -> bool:
        async with self._uow as uow:
            logger.info("Accepting mutual like: tg_id=%s to tg_id=%s", liker_tg_id, liked_tg_id)
            result = await uow.likes.accept(liker_tg_id, liked_tg_id)
            await uow.commit()
            return result
