from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.feedback import Feedback
    from app.models.route_stop import RouteStop
    from app.models.route_service_type import RouteServiceType
    from app.models.shuttle import Shuttle


class Route(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "routes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_routes_code"),
        CheckConstraint(
            "estimated_duration_minutes IS NULL OR estimated_duration_minutes > 0",
            name="ck_routes_duration_positive",
        ),
        Index("ix_routes_is_active", "is_active"),
        Index("ix_routes_service_area", "service_area"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
        back_populates="route",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RouteStop.position",
    )
    shuttles: Mapped[list[Shuttle]] = relationship(back_populates="route")
    feedback: Mapped[list[Feedback]] = relationship(back_populates="route")
    service_types: Mapped[list[RouteServiceType]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RouteServiceType.service_type",
    )
