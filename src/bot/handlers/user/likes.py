import asyncio

from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from src.bot.keyboards.inline import view_likes_menu_keyboard, pending_like_action_keyboard
from src.bot.keyboards.reply import main_menu_keyboard
from src.bot.notifiers.match_notifier import send_like_notification, send_match_notification
from src.bot.states import ViewLikesStates, UserRoadmap
from src.bot.utils.telegram_helpers import get_telegram_username_or_name
from src.repositories.uow import UnitOfWork
from src.schemas.profile import ProfileSchema
from src.services.complain_service import ComplainService
from src.services.like_service import LikeService
from src.services.profile_service import ProfileService

like_router = Router()


@like_router.callback_query(F.data.startswith("like:"))
async def handle_like(
    callback: CallbackQuery,
    like_service: LikeService,
    bot: Bot,
    state: FSMContext
):
    liker_tg_id = callback.from_user.id
    liked_tg_id = int(callback.data.split(":")[1])

    result = await like_service.like_profile(liker_tg_id, liked_tg_id)

    if not result.is_match:
        await callback.message.answer("Лайк отправлен!")
        await send_like_notification(bot, result.liker_profile, liked_tg_id)

    else:
        await callback.message.answer("🎉 У вас взаимная симпатия!")

        await asyncio.gather(
            send_match_notification(bot, result.liked_profile, liker_tg_id, liked_tg_id),
            send_match_notification(bot, result.liker_profile, liked_tg_id, liker_tg_id),
        )




@like_router.message(F.text == "Мои лайки ❤️")
async def my_likes_menu_entry(message: Message, state: FSMContext):
    await state.set_state(ViewLikesStates.choose_view_type)

    await message.answer(
        "Переходим в меню лайков...",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        "Здесь ты можешь посмотреть, кто проявил к тебе симпатию или ответил на твою",
        reply_markup=view_likes_menu_keyboard()
    )


@like_router.callback_query(ViewLikesStates.choose_view_type, F.data == "view_who_liked_me")
async def process_view_who_liked_me(callback_query: CallbackQuery, state: FSMContext, bot: Bot, uow: UnitOfWork):
    await callback_query.answer()
    user_tg_id = callback_query.from_user.id

    profile_service = ProfileService(uow)
    liker_profiles: list[ProfileSchema] = await profile_service.get_pending_liker_profiles(user_tg_id)

    if not liker_profiles:
        await callback_query.message.answer("У тебя пока нет лайков.")
        await state.set_state(ViewLikesStates.choose_view_type)
        await callback_query.message.answer("Выберите опцию:", reply_markup=view_likes_menu_keyboard())
        return

    await state.update_data(
        liker_profiles=[p.model_dump(mode="json") for p in liker_profiles],
        current_pending_index=0
    )
    await state.set_state(ViewLikesStates.viewing_pending_likes)

    await callback_query.message.edit_text("Загружаю анкеты тех, кто вас лайкнул...")
    await show_next_pending_like_profile(callback_query.message, state, bot)


async def show_next_pending_like_profile(target_message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    raw_profiles = data.get("liker_profiles", [])
    liker_profiles = [ProfileSchema.model_validate(p) for p in raw_profiles]
    current_pending_index: int = data.get("current_pending_index", 0)

    while current_pending_index < len(liker_profiles):
        profile_to_show = liker_profiles[current_pending_index]

        if profile_to_show is None:
            current_pending_index += 1
            continue

        try:
            await target_message.answer_photo(
                photo=profile_to_show.s3_path,
                caption=(
                    f"Вам симпатизирует: {profile_to_show.name}, {profile_to_show.age}, {profile_to_show.town}\n"
                    f"{profile_to_show.sex.value}\n"
                    f"{profile_to_show.description}\n\n"
                ),
                reply_markup=pending_like_action_keyboard(liker_tg_id=profile_to_show.tg_id),
            )
            await state.update_data(
                current_pending_index=current_pending_index,
                currently_viewed_pending_likes=profile_to_show.tg_id,
            )
            return
        except TelegramBadRequest as e:
            await target_message.answer(f"Произошла ошибка при показе профиля: {e}. Пропускаем...")
            current_pending_index += 1
    await target_message.answer(
        "Вы просмотрели все анкеты, которые вас лайкнули в этой сессии.",
        reply_markup=view_likes_menu_keyboard(),
    )
    await state.set_state(ViewLikesStates.choose_view_type)


@like_router.callback_query(F.data.startswith("reject_pending_like:"))
async def process_reject_pending_like(callback: CallbackQuery, state: FSMContext, uow: UnitOfWork, bot: Bot):
    await callback.answer("Лайк отклонен 👎")

    liker_tg_id = int(callback.data.split(":")[1])
    current_user_tg_id = callback.from_user.id

    like_service = LikeService(uow)
    await like_service.reject_like(liker_tg_id, current_user_tg_id)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    data = await state.get_data()
    current_pending_index = data.get("current_pending_index", 0)
    await state.update_data(current_pending_index=current_pending_index + 1)
    await show_next_pending_like_profile(callback.message, state, bot)


@like_router.callback_query(F.data.startswith("Black_list:"))
async def process_black_list(callback: CallbackQuery, state: FSMContext, uow: UnitOfWork, bot: Bot):
    await callback.answer("Пользователь добавлен в черный список 📓")

    liker_tg_id = int(callback.data.split(":")[1])
    current_user_tg_id = callback.from_user.id

    like_service = LikeService(uow)
    complain_service = ComplainService(uow)
    await like_service.reject_like(liker_tg_id, current_user_tg_id)
    await complain_service.report_profile(current_user_tg_id, liker_tg_id)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    data = await state.get_data()
    current_pending_index = data.get("current_pending_index", 0)
    await state.update_data(current_pending_index=current_pending_index + 1)
    await show_next_pending_like_profile(callback.message, state, bot)

@like_router.callback_query(ViewLikesStates.viewing_pending_likes, F.data == "next_pending_like")
async def process_next_pending_like(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    data = await state.get_data()
    current_pending_index = data.get("current_pending_index", 0)
    await state.update_data(current_pending_index=current_pending_index + 1)
    await show_next_pending_like_profile(callback.message, state, bot)


@like_router.callback_query(ViewLikesStates.choose_view_type, F.data == "view_my_mutual_likes")
async def process_view_my_mutual_likes(callback: CallbackQuery, state: FSMContext, bot: Bot, uow: UnitOfWork):
    await callback.answer()
    user_tg_id = callback.from_user.id
    profile_service = ProfileService(uow)

    liker_profiles: list[ProfileSchema] = await profile_service.get_mutual_liker_profiles(user_tg_id)

    for profile in liker_profiles:
        if profile:
            try:
                file_id = profile.s3_path
                telegram_user_info = await get_telegram_username_or_name(bot, profile.tg_id)

                await callback.message.answer_photo(
                    photo=file_id,
                    caption=(
                        f"Взаимная симпатия с: {profile.name}, {profile.age}\n"
                        f"{profile.sex.value}\n"
                        f"Город: {profile.town}\n"
                        f"О себе: {profile.description}\n\n"
                        f"Связь: {telegram_user_info}"
                    )
                )
            except TelegramBadRequest as e:
                await callback.message.answer(f"Произошла ошибка: {e}, сообщите в @SvinderSupportBot")

        else:
            await callback.message.answer("Не удалось найти один из профилей взаимных симпатий.")

        await asyncio.sleep(0.5)

    await callback.message.answer("🔼 Вот все твои взаимные лайки 🔼", reply_markup=view_likes_menu_keyboard())
    await state.set_state(ViewLikesStates.choose_view_type)


@like_router.callback_query(F.data.startswith("accept_pending_like:"))
async def process_accept_pending_like(callback: CallbackQuery, bot: Bot, uow: UnitOfWork, state: FSMContext):
    await callback.answer("Лайк принят! ❤️")
    await callback.message.delete()

    liker_tg_id = int(callback.data.split(":")[1])
    current_user_tg_id = callback.from_user.id

    profile_service = ProfileService(uow)
    like_service = LikeService(uow)

    liker_profile = await profile_service.get_profile_by_tg_id(liker_tg_id)
    current_profile = await profile_service.get_profile_by_tg_id(current_user_tg_id)

    if liker_profile is None or current_profile is None:
        await callback.message.answer("Не удалось найти один из профилей. Попробуйте позже.")
        return

    result = await like_service.accept_mutual(liker_profile.tg_id, current_profile.tg_id)


    if result:
        await asyncio.gather(
            send_match_notification(bot, liker_profile, current_profile.tg_id, liker_profile.tg_id),
            send_match_notification(bot, current_profile, liker_profile.tg_id, current_profile.tg_id),
        )



    else:

        await callback.message.answer("Не удалось подтвердить симпатию. Возможно, лайк уже был обработан.")

    data = await state.get_data()
    current_index = data.get("current_pending_index", 0)
    await state.update_data(current_pending_index=current_index + 1)
    await show_next_pending_like_profile(callback.message, state, bot)


@like_router.callback_query(F.data.in_({"likes_to_main_menu", "back_to_view_likes_menu"}))
async def process_back_buttons_like(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action = callback.data

    if action == "likes_to_main_menu":
        try:
            await callback.message.edit_text("Возвращаемся в главное меню.")
        except TelegramBadRequest:
            await callback.message.delete()

        await callback.message.answer("Окей, возвращаю!", reply_markup=main_menu_keyboard())
        await state.set_state(UserRoadmap.main_menu)

    else:
        await state.set_state(ViewLikesStates.choose_view_type)
        await callback.message.delete()
        await callback.message.answer("Меню лайков:", reply_markup=view_likes_menu_keyboard())


@like_router.callback_query(F.data.startswith("hide_profile"))
async def process_hide_profile(callback: CallbackQuery):
    await callback.message.delete()



