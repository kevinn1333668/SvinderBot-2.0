from aiogram import BaseMiddleware

from src.repositories.uow import UnitOfWork


class UoWMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def __call__(self, handler, event, data):
        data["uow"] = UnitOfWork(self.session_maker)
        return await handler(event, data)

