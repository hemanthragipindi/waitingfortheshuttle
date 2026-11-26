from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.route_stop import RouteStop


class Stop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stops"
    __table_args__ = (
        UniqueConstraint("name", name="uq_stops_name"),
        Index("ix_stops_is_active", "is_active"),
        Index("ix_stops_service_area", "service_area"),
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_area: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'LPU'")
    )
    verification_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'VERIFIED'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )

    route_stops: Mapped[list[RouteStop]] = relationship(
        back_populates="stop",
        passive_deletes=True,
    )
    feedback: Mapped[list[Feedback]] = relationship(back_populates="stop")
