from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.keyboards.reply import welcome_keyboard, main_menu_keyboard
from src.bot.states import UserRoadmap
from src.repositories.uow import UnitOfWork
from src.services.profile_service import ProfileService
from src.services.user_service import UserService
from src.static.text.texts import WELCOME_IMAGE, WELCOME_TEXT, TEXT_MAIN_MENU

commands_router = Router()


@commands_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext, uow: UnitOfWork):
    await state.clear()

    user_service = UserService(uow)
    await user_service.register_if_new(message.from_user.id, message.from_user.username)
    profile_service = ProfileService(uow)
    profile = await profile_service.get_profile_by_tg_id(message.from_user.id)

    await state.set_state(UserRoadmap.main_menu)

    if profile is None:
        await message.answer_photo(
            photo=WELCOME_IMAGE,
            caption=WELCOME_TEXT,
            reply_markup=welcome_keyboard(),
        )

    else:
        await message.answer(
            TEXT_MAIN_MENU,
            reply_markup=main_menu_keyboard(),
        )