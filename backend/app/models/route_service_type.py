from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RouteServiceType(Base):
    __tablename__ = "route_service_types"

    route_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    service_type: Mapped[str] = mapped_column(String(32), primary_key=True)
