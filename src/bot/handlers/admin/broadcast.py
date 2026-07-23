import asyncio

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.states import AdminStates
from src.core.config import settings
from src.repositories.uow import UnitOfWork
from src.services.user_service import UserService

broadcast_router = Router()


@broadcast_router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in settings.ADMINS_IDS:
        await message.answer("У вас нет прав на это действие")
        return

    await state.set_state(AdminStates.waiting_broadcast)
    await message.answer("📢 Отправь мне сообщение, которое нужно разослать всем пользователям.")


@broadcast_router.message(AdminStates.waiting_broadcast)
async def handle_broadcast(message: Message, bot: Bot, state: FSMContext, uow: UnitOfWork):
    await state.clear()

    user_service = UserService(uow)
    tg_ids = await user_service.get_all_tg_ids()

    await message.answer(f"Начинаем рассылку ({len(tg_ids)} пользователям)")

    for tg_id in tg_ids:
        try:
            if message.text:
                await bot.send_message(
                    chat_id=tg_id,
                    text=message.text
                )
            else:
                await bot.copy_message(
                    chat_id=tg_id,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id,
                    caption=message.caption or ""
                )
            await asyncio.sleep(0.05)
        except TelegramBadRequest:
            pass

    await message.answer('✅ Рассылка завершена!')
