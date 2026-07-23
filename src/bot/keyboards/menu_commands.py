from aiogram import Bot
from aiogram.types import MenuButtonCommands, BotCommand

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Меню")
    ]
    await bot.set_my_commands(commands)

async def set_menu_button(bot: Bot):
    await bot.set_chat_menu_button(
        menu_button=MenuButtonCommands(type="commands")
    )