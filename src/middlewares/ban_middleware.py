from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update

from src.repositories.uow import UnitOfWork
from src.services.ban_service import BanService


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        from_user = self._extract_user(event)

        if from_user is None:
            return await handler(event, data)

        uow: UnitOfWork = data["uow"]
        ban_service = BanService(uow)
        is_banned = await ban_service.is_banned(from_user.id)

        if is_banned:
            if isinstance(event, Message):
                await event.answer("❌ Вы забанены и не можете использовать бота.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Вы забанены.", show_alert=True)
            return

        return await handler(event, data)

    @staticmethod
    def _extract_user(event: TelegramObject):
        if hasattr(event, "from_user") and event.from_user:
            return event.from_user
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                return event.message.from_user
            if event.callback_query and event.callback_query.from_user:
                return event.callback_query.from_user
        return None