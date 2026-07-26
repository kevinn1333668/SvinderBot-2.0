import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.repositories.uow import UnitOfWork

logger = logging.getLogger(__name__)

async def cleanup_expired_dislikes(session_maker):
    async with session_maker() as session:
        uow = UnitOfWork(session_maker)
        async with uow as u:
            deleted = await u.dislikes.delete_expired()
            await u.commit()
            logger.info("Cleaned up %d expired dislikes", deleted)

def setup_scheduler(session_maker):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cleanup_expired_dislikes, "interval", hours=24, args=[session_maker])
    scheduler.start()