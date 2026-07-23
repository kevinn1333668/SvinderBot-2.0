from aiogram import Bot


async def get_telegram_username_or_name(bot: Bot, tg_id: int) -> str:
    chat = await bot.get_chat(tg_id)
    if chat.username:
        return f"@{chat.username}"
    return f"@{chat.first_name or ''} {chat.last_name or ''}".strip() or str(tg_id)