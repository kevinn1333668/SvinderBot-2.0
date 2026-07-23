from sqlalchemy.ext.asyncio import async_sessionmaker

from src.repositories.ban_repo import BanRepository
from src.repositories.complain_repo import ComplainRepository
from src.repositories.dislike_repo import DislikeRepository
from src.repositories.like_repo import LikeRepository
from src.repositories.profile_repo import ProfileRepository
from src.repositories.user_repo import UserRepository




class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def __aenter__(self):
        self.session = self.session_factory()
        self.users = UserRepository(self.session)
        self.profiles = ProfileRepository(self.session)
        self.bans = BanRepository(self.session)
        self.likes = LikeRepository(self.session)
        self.dislikes = DislikeRepository(self.session)
        self.complains = ComplainRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()