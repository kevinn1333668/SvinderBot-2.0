from typing import Annotated
from datetime import datetime

from sqlalchemy import text, Boolean, Integer, ForeignKey, DateTime, String, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.schemas.enums import SexEnum, SexFilterState
from src.core.db import Base


created_at_type = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
]

modified_at_type = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
]



class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"), unique=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[SexEnum] = mapped_column(nullable=False)
    town: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text('true')
    )

    s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    sex_filter: Mapped[SexFilterState] = mapped_column(
        SQLEnum(SexFilterState, name="sex_filter_state", native_enum=True),
        nullable=False,
        default=SexFilterState.OFF,
    )

    created_at: Mapped[created_at_type]
    modified_at: Mapped[modified_at_type]

    user: Mapped["User"] = relationship(back_populates="profile")