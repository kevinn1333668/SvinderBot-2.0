import logging

from src.repositories.models import Ban
from src.repositories.uow import UnitOfWork

logger = logging.getLogger(__name__)

class BanService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def is_banned(self, tg_id: int) -> bool:
        async with self._uow as uow:
            return await uow.bans.is_banned(tg_id)

    async def is_banned_by_ban_id(self, ban_id: int) -> bool:
        async with self._uow as uow:
            return await uow.bans.is_banned_by_ban_id(ban_id)

    async def ban_user(self, tg_id: int) -> Ban | None:
        async with self._uow as uow:
            if await uow.bans.is_banned(tg_id):
                return None

            user_exists = await uow.users.exists_by_tg_id(tg_id)
            if not user_exists:
                return None

            logger.info("Creating ban for tg_id=%s", tg_id)

            ban = await uow.bans.create(tg_id)
            await uow.profiles.delete(tg_id)
            await uow.commit()
            return ban


    async def unban_user(self, ban_id: int) -> bool:
        async with self._uow as uow:
            logger.info("Unbanning ban_id=%s", ban_id)
            result = await uow.bans.unban(ban_id)
            await uow.commit()

            return result

    async def get_ban_by_ban_id(self, ban_id: int) -> Ban | None:
        async with self._uow as uow:
            if await uow.bans.is_banned_by_ban_id(ban_id):
                return await uow.bans.get(ban_id)
            return None

