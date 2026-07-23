import logging

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def __call__(self, handler, event, data):
        if isinstance(handler, Message):
            logger.info("Message from tg_id=%s: %r", event.tg_id, event.text)
        return await handler(event, data)