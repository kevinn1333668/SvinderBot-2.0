from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Complain(Base):
    __tablename__ = 'complaints'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    complainant_tg_id: Mapped[int] = mapped_column(ForeignKey("profiles.tg_id", ondelete="CASCADE"), nullable=False)
    reported_tg_id: Mapped[int] = mapped_column(ForeignKey("profiles.tg_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("complainant_tg_id", "reported_tg_id", name="uq_complainant_reported"),
    )