import logging

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.repositories.uow import UnitOfWork

logger = logging.getLogger(__name__)

class ComplainService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def report_profile(self, complainant_tg_id: int, reported_tg_id: int) -> bool:
        async with self._uow as uow:
            try:
                logger.info("Report profile (tg_id=%s) from user (tg_id=%s)", reported_tg_id, complainant_tg_id)
                result = await uow.complains.create(complainant_tg_id, reported_tg_id)
                await uow.commit()
                return result
            except IntegrityError:
                logger.exception("Failed to report profile tg_id=%s", reported_tg_id)
                await uow.rollback()
                return False