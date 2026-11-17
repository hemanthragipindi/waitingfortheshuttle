import uuid
from datetime import datetime

from pydantic import Field

from app.core.enums import ShuttleServiceStatus
from app.schemas.common import ORMModel
from app.schemas.shuttles import ShuttleRead


class ShuttleStatusCreate(ORMModel):
    shuttle_id: uuid.UUID
    status: ShuttleServiceStatus
    message: str | None = Field(default=None, max_length=2000)


class ShuttleStatusRead(ORMModel):
    id: uuid.UUID
    shuttle_id: uuid.UUID
    shuttle: ShuttleRead
    status: ShuttleServiceStatus
    message: str | None
    created_at: datetime
    updated_at: datetime


class ShuttleStatusCurrentRead(ORMModel):
    shuttle: ShuttleRead
    status_update_id: uuid.UUID | None
    status: ShuttleServiceStatus
    message: str | None
    last_updated_at: datetime | None
