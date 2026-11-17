from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.route import Route
    from app.models.shuttle_status import ShuttleStatus


class Shuttle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shuttles"
    __table_args__ = (
        UniqueConstraint("vehicle_code", name="uq_shuttles_vehicle_code"),
        CheckConstraint("capacity > 0", name="ck_shuttles_capacity_positive"),
        Index("ix_shuttles_route_id", "route_id"),
        Index("ix_shuttles_is_active", "is_active"),
    )

    vehicle_code: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
    )

    route: Mapped[Route | None] = relationship(back_populates="shuttles")
    status_updates: Mapped[list[ShuttleStatus]] = relationship(
        back_populates="shuttle",
        passive_deletes=True,
        order_by="ShuttleStatus.created_at.desc()",
    )
    feedback: Mapped[list[Feedback]] = relationship(back_populates="shuttle")
