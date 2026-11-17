from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ORMModel


class RouteCreate(ORMModel):
    code: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, gt=0)
    stop_ids: list[UUID] = Field(default_factory=list)

    @field_validator("stop_ids")
    @classmethod
    def stop_ids_must_be_unique(cls, values: list[UUID]) -> list[UUID]:
        if len(values) != len(set(values)):
            raise ValueError("A stop can appear only once in a route.")
        return values


class RouteUpdate(ORMModel):
    code: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    stop_ids: list[UUID] | None = None

    @field_validator("code", "name")
    @classmethod
    def text_fields_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("This field cannot be null.")
        return value

    @field_validator("is_active")
    @classmethod
    def active_flag_cannot_be_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("is_active cannot be null.")
        return value

    @field_validator("stop_ids")
    @classmethod
    def stop_ids_must_be_unique(cls, values: list[UUID] | None) -> list[UUID] | None:
        if values is not None and len(values) != len(set(values)):
            raise ValueError("A stop can appear only once in a route.")
        return values


class StopSummary(ORMModel):
    id: UUID
    name: str
    is_active: bool


class RouteStopRead(ORMModel):
    stop_id: UUID
    position: int
    stop: StopSummary


class RouteRead(ORMModel):
    id: UUID
    code: str
    name: str
    estimated_duration_minutes: int | None
    is_active: bool
    route_stops: list[RouteStopRead]


class RouteStopAdd(ORMModel):
    stop_id: UUID
    position: int | None = Field(default=None, gt=0)


class RouteStopOrder(ORMModel):
    stop_ids: list[UUID]

    @field_validator("stop_ids")
    @classmethod
    def stop_ids_must_be_unique(cls, values: list[UUID]) -> list[UUID]:
        if len(values) != len(set(values)):
            raise ValueError("A stop can appear only once in a route.")
        return values
