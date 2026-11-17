import uuid

from pydantic import Field, field_validator

from app.schemas.common import ORMModel


class ShuttleCreate(ORMModel):
    vehicle_code: str = Field(min_length=1, max_length=32)
    capacity: int = Field(gt=0)
    route_id: uuid.UUID | None = None


class ShuttleUpdate(ORMModel):
    vehicle_code: str | None = Field(default=None, min_length=1, max_length=32)
    capacity: int | None = Field(default=None, gt=0)
    route_id: uuid.UUID | None = None
    is_active: bool | None = None

    @field_validator("vehicle_code")
    @classmethod
    def vehicle_code_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("vehicle_code cannot be null.")
        return value

    @field_validator("capacity")
    @classmethod
    def capacity_cannot_be_null(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("capacity cannot be null.")
        return value

    @field_validator("is_active")
    @classmethod
    def active_flag_cannot_be_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("is_active cannot be null.")
        return value


class ShuttleRead(ORMModel):
    id: uuid.UUID
    vehicle_code: str
    capacity: int
    route_id: uuid.UUID | None
    is_active: bool
