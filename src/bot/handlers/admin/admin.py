from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from src.bot.utils.telegram_helpers import get_telegram_username_or_name
from src.core.config import settings
from src.repositories.uow import UnitOfWork
from src.services.ban_service import BanService
from src.services.user_service import UserService

admin_router = Router()


@admin_router.callback_query(F.data.startswith("approve_"))
async def handle_approve(callback_query: CallbackQuery, bot: Bot):
    await callback_query.answer()

    user_tg_id = int(callback_query.data.split("_")[1])
    admin = callback_query.from_user

    username = await get_telegram_username_or_name(bot, user_tg_id)

    admin_mention = f"@{admin.username}" if admin.username else admin.full_name

    new_text = f"✅ Админ {admin_mention} одобрил пользователя {username}"

    try:
        await callback_query.message.delete()
    except TelegramBadRequest:
        pass

    await callback_query.message.answer(new_text)


@admin_router.callback_query(F.data.startswith("ban_"))
async def handle_ban(callback_query: CallbackQuery, bot: Bot, uow: UnitOfWork):
    await callback_query.answer()

    action = callback_query.data
    user_tg_id = int(action.split("_")[1])

    if user_tg_id in settings.ADMINS_IDS:
        await callback_query.message.delete()
        await callback_query.message.answer("Нельзя забанить администратора")
        return

    ban_service = BanService(uow)
    is_banned = await ban_service.is_banned(user_tg_id)

    if is_banned:
        await callback_query.message.answer("Пользователь уже забанен")
        return

    ban = await ban_service.ban_user(user_tg_id)

    if ban is None:
        await callback_query.message.answer("Не удалось забанить пользователя (не найден).")
        return

    admin = callback_query.from_user
    username = await get_telegram_username_or_name(bot, user_tg_id)
    admin_mention = f"@{admin.username}" if admin.username else admin.full_name

    new_text = f"❌ Админ {admin_mention} забанил пользователя {username}. ID бана - {ban.id}"

    try:
        await bot.send_message(
            chat_id=user_tg_id,
            text=f"Вы забаненны по решению администрации. ID бана {ban.id}\n По всем вопросам - @SvinderSupportBot"
        )
    except TelegramBadRequest:
        pass

    await callback_query.message.delete()
    await callback_query.message.answer(new_text)


@admin_router.message(Command("ban"))
async def command_ban(message: Message, command: CommandObject, bot: Bot, uow: UnitOfWork):
    if message.from_user.id not in settings.ADMINS_IDS:
        await message.answer("У вас нет прав на это действие")
        return

    args = command.args

    if not args:
        await message.answer("Укажите username. Пример: /ban durov")
        return

    username = args.strip().lstrip("@")
    user_service = UserService(uow)

    user = await user_service.get_user_by_username(username)

    if user is None:
        await message.answer(f"❌ Пользователь @{username} не найден")
        return

    if user.tg_id in settings.ADMINS_IDS:
        await message.answer("Нельзя забанить администратора")
        return

    ban_service = BanService(uow)
    ban = await ban_service.ban_user(user.tg_id)
    if ban:
        await message.answer(f"✅ Пользователь @{username} забанен. ID бана - {ban.id}")

        try:
            await message.bot.send_message(user.tg_id,
                                           f"❌ Вы были забанены по решению администрации. ID бана - {ban.id}\n По всем вопросам обращаться в @SvinderSupportBot"
                                           )
        except TelegramBadRequest:
            pass
    else:
        await message.answer("❌ Пользователь уже забанен или не существует")


@admin_router.message(Command("unban"))
async def command_unban(message: Message, command: CommandObject, bot: Bot, uow: UnitOfWork):
    if message.from_user.id not in settings.ADMINS_IDS:
        await message.answer("У вас нет прав на это действие")
        return


    args = command.args

    if not args or not args.isdigit() or int(args) < 1:
        await message.answer("❌ ID должен быть целым числом\n Пример команды: /unban 1")
        return

    ban_service = BanService(uow)
    ban = await ban_service.get_ban_by_ban_id(int(args))
    if ban is None:
        await message.answer("❌ Пользователь не забанен или не существует")
        return
    is_unbanned = await ban_service.unban_user(ban.id)

    if is_unbanned:
        await message.answer(f"✅ Пользователь разбанен")

        try:
            await message.bot.send_message(
                ban.tg_id,
                "✅ Вы были разбанены по решению администрации"
            )
        except TelegramBadRequest:
            pass
    else:
        await message.answer("❌ Ошибка при разбане")
