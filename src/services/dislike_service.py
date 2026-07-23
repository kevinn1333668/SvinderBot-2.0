import logging
from logging import Logger

from src.repositories.uow import UnitOfWork
from src.core.config import settings

logger = logging.getLogger(__name__)

class DislikeService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def dislike_profile(self, disliker_tg_id: int, disliked_tg_id: int) -> bool:
        async with self._uow as uow:
            logger.info("Creating dislike: %s to %s", disliker_tg_id, disliked_tg_id)
            result = await uow.dislikes.create(disliker_tg_id, disliked_tg_id, settings.COOLDOWN)
            await uow.commit()
            return result