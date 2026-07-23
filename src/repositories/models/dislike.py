from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Dislike(Base):
    __tablename__ = "dislikes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disliker_tg_id: Mapped[int] = mapped_column(ForeignKey("profiles.tg_id", ondelete="CASCADE"), nullable=False)
    disliked_tg_id: Mapped[int] = mapped_column(ForeignKey("profiles.tg_id", ondelete="CASCADE"), nullable=False)

    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("disliker_tg_id", "disliked_tg_id", name="uq_dislike_tg_id"),
    )