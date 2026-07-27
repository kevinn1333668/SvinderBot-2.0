from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.bot.utils.telegram_helpers import get_telegram_username_or_name
from src.schemas.profile import ProfileSchema


async def send_match_notification(
        bot: Bot,
        profile_to_show: ProfileSchema,
        to_tg_id: int,
        other_tg_id: int,
) -> None:
    contact_info = await get_telegram_username_or_name(bot, other_tg_id)
    try:
        await bot.send_photo(
            chat_id=to_tg_id,
            photo=profile_to_show.s3_path,
            caption=(
                f"Взаимная симпатия с: {profile_to_show.name}, {profile_to_show.age}\n"
                f"Город: {profile_to_show.town}\n"
                f"О себе: {profile_to_show.description}\n\n"
                f"Связь: {contact_info}"
            ),
        )
    except TelegramBadRequest:
        await bot.send_message(
            to_tg_id,
            f"Не удалось загрузить фото профиля {profile_to_show.name}."
        )
    except Exception as e:
        await bot.send_message(
            to_tg_id,
            f"Ошибка при показе профиля {profile_to_show.name}."
        )
        print(f"Error sending mutual like profile: {e}")


async def send_like_notification(
        bot: Bot,
        liker_profile: ProfileSchema,
        liked_tg_id: int,
) -> None:
    try:
        await bot.send_photo(
            chat_id=liked_tg_id,
            photo=liker_profile.s3_path,
            caption=(
                f"Вас лайкнул: {liker_profile.name}, {liker_profile.age}\n"
                f"{liker_profile.sex.value}\n"
                f"Город: {liker_profile.town}\n"
                f"О себе: {liker_profile.description}\n\n"
            )
        )
    except FileNotFoundError:
        await bot.send_message(
            liked_tg_id,
            f"Не удалось загрузить фото профиля {liker_profile.name}."
        )
    except Exception as e:
        await bot.send_message(
            liked_tg_id,
            f"Ошибка при показе профиля {liker_profile.name}."
        )
        print(f"Error sending mutual like profile: {e}")