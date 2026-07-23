from sqlite3 import IntegrityError

from src.repositories.base import BaseRepository
from src.repositories.models import Complain


class ComplainRepository(BaseRepository):
    async def create(self, complainant_tg_id: int, reported_tg_id: int) -> bool:
        complain = Complain(
            complainant_tg_id=complainant_tg_id,
            reported_tg_id=reported_tg_id
        )
        self.session.add(complain)
        await self.session.flush()
        return True