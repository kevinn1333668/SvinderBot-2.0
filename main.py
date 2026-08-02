import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.handlers.admin.broadcast import broadcast_router
from src.bot.utils.scheduled_tasks import setup_scheduler
from src.core.config import settings
from src.core.db import async_session as session_maker
from src.core.logging_settings import setup_logging
from src.middlewares.uow_middleware import UoWMiddleware
from src.middlewares.ban_middleware import BanCheckMiddleware
from src.middlewares.logging_middleware import LoggingMiddleware

from src.bot.handlers.admin.admin import admin_router
from src.bot.handlers.user.command import commands_router
from src.bot.handlers.user.user import user_router
from src.bot.handlers.user.search import search_router
from src.bot.handlers.user.edit_profile import edit_router
from src.bot.handlers.user.likes import like_router
from src.bot.handlers.user.create_profile import profile_router

from src.bot.keyboards.menu_commands import setup_bot_commands, set_menu_button


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    dp.message.middleware(LoggingMiddleware(session_maker))
    dp.message.middleware(UoWMiddleware(session_maker))
    dp.callback_query.middleware(UoWMiddleware(session_maker))


    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    dp.include_routers(
        admin_router,
        broadcast_router,
        commands_router,
        search_router,
        edit_router,
        like_router,
        user_router,
        profile_router
    )

    setup_scheduler(session_maker)

    await setup_bot_commands(bot)
    await set_menu_button(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    setup_logging(level=settings.LOG_LEVEL)
    asyncio.run(main())