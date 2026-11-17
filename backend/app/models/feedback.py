from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.route import Route
    from app.models.shuttle import Shuttle
    from app.models.stop import Stop
    from app.models.user import User


class Feedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "category IN ('DELAY', 'OVERCROWDING', 'INCORRECT_STOP', 'SUGGESTION', 'OTHER')",
            name="ck_feedback_category",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'IN_REVIEW', 'RESOLVED', 'DISMISSED')",
            name="ck_feedback_status",
        ),
        CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5",
            name="ck_feedback_rating_range",
        ),
        Index("ix_feedback_status_created", "status", "created_at"),
        Index("ix_feedback_user_id", "user_id"),
        Index("ix_feedback_route_id", "route_id"),
        Index("ix_feedback_stop_id", "stop_id"),
        Index("ix_feedback_shuttle_id", "shuttle_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )
    admin_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    stop_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("stops.id", ondelete="SET NULL"),
        nullable=True,
    )
    shuttle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("shuttles.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    submitted_by: Mapped[User] = relationship(
        back_populates="feedback_submitted",
        foreign_keys=[user_id],
    )
    reviewed_by: Mapped[User | None] = relationship(
        back_populates="feedback_reviewed",
        foreign_keys=[reviewed_by_id],
    )
    route: Mapped[Route | None] = relationship(back_populates="feedback")
    stop: Mapped[Stop | None] = relationship(back_populates="feedback")
    shuttle: Mapped[Shuttle | None] = relationship(back_populates="feedback")
