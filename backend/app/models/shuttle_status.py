from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.shuttle import Shuttle
    from app.models.user import User


class ShuttleStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shuttle_status"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ON_TIME', 'DELAYED', 'UNAVAILABLE', 'NOT_UPDATED')",
            name="ck_shuttle_status_value",
        ),
        Index("ix_shuttle_status_shuttle_created", "shuttle_id", "created_at"),
    )

    shuttle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shuttles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    shuttle: Mapped[Shuttle] = relationship(back_populates="status_updates")
    updated_by: Mapped[User | None] = relationship(back_populates="status_updates")
