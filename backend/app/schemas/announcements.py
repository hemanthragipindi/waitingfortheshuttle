import uuid
from datetime import datetime, timezone

from pydantic import Field, field_validator, model_validator

from app.schemas.common import ORMModel


def _validate_timezone(value: datetime | None) -> datetime | None:
    if value is not None and value.utcoffset() is None:
        raise ValueError("Announcement dates must include a timezone.")
    return value


class AnnouncementCreate(ORMModel):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1)
    is_published: bool = False
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("title", "body")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("starts_at", "ends_at")
    @classmethod
    def dates_require_timezone(cls, value: datetime | None) -> datetime | None:
        return _validate_timezone(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "AnnouncementCreate":
        if (
            self.starts_at
            and self.ends_at
            and self.ends_at.astimezone(timezone.utc)
            <= self.starts_at.astimezone(timezone.utc)
        ):
            raise ValueError("ends_at must be later than starts_at.")
        return self


class AnnouncementUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    body: str | None = Field(default=None, min_length=1)
    is_published: bool | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("title", "body")
    @classmethod
    def text_cannot_be_blank_or_null(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("is_published")
    @classmethod
    def publication_flag_cannot_be_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("is_published cannot be null.")
        return value

    @field_validator("starts_at", "ends_at")
    @classmethod
    def dates_require_timezone(cls, value: datetime | None) -> datetime | None:
        return _validate_timezone(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "AnnouncementUpdate":
        if (
            self.starts_at
            and self.ends_at
            and self.ends_at.astimezone(timezone.utc)
            <= self.starts_at.astimezone(timezone.utc)
        ):
            raise ValueError("ends_at must be later than starts_at.")
        return self


class AnnouncementRead(ORMModel):
    id: uuid.UUID
    title: str
    body: str
    is_published: bool
    starts_at: datetime | None
    ends_at: datetime | None
    published_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
