import uuid
from datetime import datetime

from pydantic import Field

from app.core.enums import FeedbackCategory, FeedbackStatus
from app.schemas.common import ORMModel


class FeedbackCreate(ORMModel):
    category: FeedbackCategory
    message: str = Field(min_length=1, max_length=5000)
    rating: int | None = Field(default=None, ge=1, le=5)
    route_id: uuid.UUID | None = None
    stop_id: uuid.UUID | None = None
    shuttle_id: uuid.UUID | None = None


class FeedbackStatusUpdate(ORMModel):
    status: FeedbackStatus
    admin_response: str | None = Field(default=None, max_length=5000)


class FeedbackRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: FeedbackCategory
    message: str
    rating: int | None
    status: FeedbackStatus
    admin_response: str | None
    route_id: uuid.UUID | None
    stop_id: uuid.UUID | None
    shuttle_id: uuid.UUID | None
    reviewed_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
