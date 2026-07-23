from sqlalchemy import text, Boolean, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    liker_tg_id: Mapped[int] = mapped_column(ForeignKey("profiles.tg_id", ondelete="CASCADE"), nullable=False, index=True)
    liked_tg_id: Mapped[int] = mapped_column(ForeignKey("profiles.tg_id", ondelete="CASCADE"), nullable=False, index=True)

    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))

    __table_args__ = (
        UniqueConstraint("liker_tg_id", "liked_tg_id", name="uq_liker_liked"),
        CheckConstraint("liker_tg_id != liked_tg_id", name="ck_no_self_like"),
    )

