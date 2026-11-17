from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.announcement import Announcement
    from app.models.feedback import Feedback
    from app.models.shuttle_status import ShuttleStatus


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('STUDENT', 'ADMIN')", name="ck_users_role"),
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_role", "role"),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="STUDENT",
        server_default=text("'STUDENT'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    feedback_submitted: Mapped[list[Feedback]] = relationship(
        back_populates="submitted_by",
        foreign_keys="Feedback.user_id",
    )
    feedback_reviewed: Mapped[list[Feedback]] = relationship(
        back_populates="reviewed_by",
        foreign_keys="Feedback.reviewed_by_id",
    )
    announcements: Mapped[list[Announcement]] = relationship(back_populates="published_by")
    status_updates: Mapped[list[ShuttleStatus]] = relationship(back_populates="updated_by")
