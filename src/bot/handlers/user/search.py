from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from src.bot.keyboards.inline import profile_action_keyboard, show_profile_keyboard, confirm_keyboard, \
    moderation_keyboard
from src.bot.keyboards.reply import main_menu_keyboard
from src.bot.notifiers.match_notifier import send_match_notification
from src.bot.states import UserRoadmap, SearchProfileStates
from src.core.config import settings
from src.repositories.uow import UnitOfWork
from src.schemas.enums import SexFilterState
from src.services.complain_service import ComplainService
from src.services.dislike_service import DislikeService
from src.services.like_service import LikeService
from src.services.profile_service import ProfileService
from src.static.text.texts import TEXT_SEARCH_PROFILES, COMPLAINS

search_router = Router()


async def send_next_profile(
        target_message: Message,
        curr_user_tg_id: int,
        state: FSMContext,
        bot: Bot,
        sex_filter: SexFilterState,
        profile_service: ProfileService,
):
    profile = await profile_service.search_random_profile(curr_user_tg_id, sex_filter)

    if profile is None:
        await target_message.answer(
            "Других профилей не найдено 😭\nПри дизлайке профиль скрывается на некоторое время",
            reply_markup=main_menu_keyboard(),
        )
        await state.set_state(UserRoadmap.main_menu)
        return

    await state.update_data(
        current_viewing_tg_id=profile.tg_id,
        profile_image=profile.s3_path
    )

    try:
        await target_message.answer_photo(
            photo=profile.s3_path,
            caption=(
                f"{profile.name}, {profile.age}, {profile.town}\n"
                f"{profile.sex.value}\n"
                f"{profile.description}"
            ),
            reply_markup=profile_action_keyboard()
        )
        await state.set_state(SearchProfileStates.viewing_profile)

    except TelegramBadRequest:
        await target_message.answer(
            "Не удалось загрузить фото анкеты. Попробуйте /search снова."
        )
        await state.set_state(UserRoadmap.main_menu)


@search_router.callback_query(
    SearchProfileStates.viewing_profile,
    F.data.in_(["like", "next", "main_menu", "complain", "blacklist"])
)
async def handle_profile_action(
        callback_query: CallbackQuery,
        state: FSMContext,
        bot: Bot,
        uow: UnitOfWork
):
    await callback_query.answer()

    action = callback_query.data
    user_tg_id = callback_query.from_user.id
    state_data = await state.get_data()
    viewed_tg_id = state_data.get("current_viewing_tg_id")
    sex_filter = SexFilterState(state_data.get("sex_filter"))

    if not viewed_tg_id:
        await callback_query.message.answer("Ошибка состояния. Попробуйте начать поиск заново.")
        await state.clear()
        return

    like_service = LikeService(uow)
    dislike_service = DislikeService(uow)
    complain_service = ComplainService(uow)
    profile_service = ProfileService(uow)


    if action == "like":
        like_result = await like_service.like_profile(user_tg_id, viewed_tg_id)
        await callback_query.message.answer("👍")

        if like_result.is_match:
            await send_match_notification(bot, like_result.liked_profile, user_tg_id, viewed_tg_id)
            await send_match_notification(bot, like_result.liker_profile, viewed_tg_id, user_tg_id)
        else:
            await bot.send_message(
                chat_id=viewed_tg_id,
                text="Вас лайкнули! ❤️\nПосмотрите, кто это был 👀",
                reply_markup=show_profile_keyboard(user_tg_id),
            )

        await send_next_profile(callback_query.message, user_tg_id, state, bot, sex_filter, profile_service)

    elif action == "next":
        await dislike_service.dislike_profile(user_tg_id, viewed_tg_id)
        await send_next_profile(callback_query.message, user_tg_id, state, bot, sex_filter, profile_service)

    elif action == "blacklist":
        await complain_service.report_profile(user_tg_id, viewed_tg_id)
        await send_next_profile(callback_query.message, user_tg_id, state, bot, sex_filter, profile_service)

    elif action == "complain":
        await state.update_data(
            previous_message_text=callback_query.message.caption,
        )
        try:
            await callback_query.message.edit_caption(
                caption="Данная анкета будет добавлена в черный список 🛡️.\nВыберите причину жалобы",
                reply_markup=confirm_keyboard(),
            )
        except TelegramBadRequest:
            await callback_query.message.answer("Произошла ошибка. Попробуйте еще раз.")
        return

    elif action == "main_menu":
        await callback_query.message.answer("Возвращаемся в главное меню.", reply_markup=main_menu_keyboard())
        await state.set_state(UserRoadmap.main_menu)

    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


@search_router.message(F.text == TEXT_SEARCH_PROFILES)
async def initiate_profile_search_handler(
        message: Message,
        state: FSMContext,
        bot: Bot,
        uow: UnitOfWork,
):
    await state.clear()

    profile_service = ProfileService(uow)
    user_profile = await profile_service.get_profile_by_tg_id(message.from_user.id)

    if user_profile is None:
        await message.answer("Чтобы начать поиск, сначала создайте анкету (/start).")
        return

    await state.update_data(sex_filter=user_profile.sex_filter.value)
    await message.answer("Начинаем поиск анкет...", reply_markup=ReplyKeyboardRemove())

    await send_next_profile(
        message, message.from_user.id, state, bot, user_profile.sex_filter, profile_service
    )


@search_router.callback_query(F.data.startswith("complain"))
async def handle_complain_confirmation(
        callback_query: CallbackQuery,
        state: FSMContext,
        bot: Bot,
        uow: UnitOfWork,
):
    await callback_query.answer()

    action = callback_query.data
    state_data = await state.get_data()
    viewed_tg_id = state_data.get("current_viewing_tg_id")
    profile_photo = state_data.get("profile_image")
    previous_message_text = state_data.get("previous_message_text", "")
    sex_filter = SexFilterState(state_data.get("sex_filter"))

    if action == "complain_cancel":
        try:
            await callback_query.message.edit_caption(
                caption=previous_message_text,
                reply_markup=profile_action_keyboard()
            )
        except TelegramBadRequest:
            await callback_query.message.answer("Возврат к предыдущему профилю")

        await state.update_data(previous_message_text=None, previous_keyboard=None)
        return

    if not viewed_tg_id:
        await callback_query.message.answer("Ошибка состояния. Попробуйте начать поиск заново")
        await state.clear()
        return

    parts = action.split("_")
    if len(parts) < 2 or parts[1] not in COMPLAINS:
        await callback_query.message.answer("Не удалось определить причину жалобы. Попробуйте ещё раз.")
        return

    user_tg_id = callback_query.from_user.id

    complain_service = ComplainService(uow)
    profile_service = ProfileService(uow)

    await complain_service.report_profile(user_tg_id, viewed_tg_id)

    await bot.send_photo(
        chat_id=settings.ADMIN_CHAT_ID,
        photo=profile_photo,
        caption=f"{previous_message_text}\nПричина : {COMPLAINS[parts[1]]}",
        reply_markup=moderation_keyboard(viewed_tg_id),
    )

    await callback_query.message.answer("👍")

    await send_next_profile(callback_query.message, user_tg_id, state, bot, sex_filter, profile_service)