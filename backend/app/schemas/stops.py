from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ORMModel


class StopCreate(ORMModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class StopUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("name cannot be null.")
        return value

    @field_validator("is_active")
    @classmethod
    def active_flag_cannot_be_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("is_active cannot be null.")
        return value


class StopRead(ORMModel):
    id: UUID
    name: str
    description: str | None
    is_active: bool
