from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.exc import SQLAlchemyError

from src.bot.keyboards.inline import get_confirmation_keyboard, short_pending_like_action_keyboard
from src.bot.keyboards.reply import welcome_keyboard, understand_keyboard, yes_or_no_keyboard
from src.bot.states import UserRoadmap, EditProfileStates, CreateProfileStates
from src.repositories.uow import UnitOfWork
from src.schemas.enums import SexFilterState
from src.services.profile_service import ProfileService
from src.static.text.texts import TEXT_MY_PROFILE, TEXT_FILTER_SEX, TEXT_DELETE_PROFILE, TEXT_EDIT_PROFILE, TEXT_YES, \
    TEXT_PROFILE_CREATE_BEGIN

user_router = Router()


@user_router.message(F.text == TEXT_MY_PROFILE)
async def get_my_profile(message: Message, uow: UnitOfWork):
    profile_service = ProfileService(uow)
    profile = await profile_service.get_profile_by_tg_id(message.from_user.id)

    if profile is None:
        await message.answer("У тебя ещё нет анкеты. Создай её через /start.")
        return

    await message.answer_photo(
        photo=profile.s3_path,
        caption=(
            f"{profile.name}, {profile.age}, {profile.town}\n"
            f"{profile.sex.value}\n"
            f"{profile.description}\n"
        )
    )


@user_router.message(F.text == TEXT_FILTER_SEX)
async def toggle_gender_filter(message: Message, uow: UnitOfWork):
    profile_service = ProfileService(uow)
    new_state = await profile_service.toggle_sex_filter(message.from_user.id)

    if new_state is None:
        await message.answer("Сначала нужно создать анкету.")
        return

    labels = {
        SexFilterState.OFF: "Фильтрация: выключена ❌",
        SexFilterState.ONLY_GIRLS: "Фильтрация: Девочки 👧",
        SexFilterState.ONLY_BOYS: "Фильтрация: Мальчики 👦",
    }
    await message.answer(labels[new_state])


@user_router.message(F.text == TEXT_DELETE_PROFILE)
async def delete_profile(message: Message):
    await message.answer(
        text="Вы уверены, что хотите удалить свой профиль? Это действие нельзя отменить.",
        reply_markup=get_confirmation_keyboard(),
    )


@user_router.callback_query(F.data == "confirm_delete_profile")
async def confirm_delete_profile(callback: CallbackQuery, uow: UnitOfWork):
    profile_service = ProfileService(uow)

    try:
        deleted = await profile_service.delete_profile(callback.from_user.id)
    except SQLAlchemyError:
        await callback.message.edit_text(text="Ошибка при удалении профиля!")
        await callback.answer()
        return

    if deleted:
        await callback.message.edit_text(text="Анкета успешно удалена! Нажмите '/start' для перезапуска.")
    else:
        await callback.message.edit_text(text="Анкета не найдена.")

    await callback.answer()


@user_router.callback_query(F.data == "cancel_delete_profile")
async def cancel_delete_profile(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@user_router.message(F.text == TEXT_EDIT_PROFILE)
async def user_start_edit_profile(message: Message, state: FSMContext):
    await message.answer(
        "Ну что же, давай отредактируем твою анкету",
        reply_markup=welcome_keyboard(),
    )
    await state.set_state(EditProfileStates.start)


@user_router.message(UserRoadmap.main_menu, F.text == TEXT_YES)
async def user_create_profile(message: Message, state: FSMContext):
    await message.answer(
        TEXT_PROFILE_CREATE_BEGIN,
        reply_markup=understand_keyboard()
    )
    await state.set_state(CreateProfileStates.start)


@user_router.message(UserRoadmap.main_menu)
async def unknown_command(message: Message, state: FSMContext):
    await message.answer(
        "Нужно создать анкету",
        reply_markup=yes_or_no_keyboard(),
    )


@user_router.callback_query(F.data.startswith("show_profile"))
async def show_liker_profile(callback: CallbackQuery, bot: Bot, uow: UnitOfWork):
    await callback.message.delete()

    liker_tg_id_to_show = int(callback.data.split(":")[1])

    profile_service = ProfileService(uow)
    profile = await profile_service.get_profile_by_tg_id(liker_tg_id_to_show)

    if profile is None:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text="Этот профиль больше не существует.",
        )
        return

    try:
        await bot.send_photo(
            chat_id=callback.from_user.id,
            photo=profile.s3_path,
            caption=(
                f"Вам симпатизирует: {profile.name}, {profile.age} лет, {profile.town}\n"
                f"{profile.description}\n\n"
            ),
            reply_markup=short_pending_like_action_keyboard(liker_tg_id=liker_tg_id_to_show),
        )
    except TelegramBadRequest:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"Не удалось загрузить фото для профиля {profile.name}. Пропускаем...",
        )