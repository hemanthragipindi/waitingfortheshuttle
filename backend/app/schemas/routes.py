from uuid import UUID

from pydantic import Field, field_validator

from app.core.enums import ServiceArea, TransportServiceType, VerificationStatus
from app.schemas.common import ORMModel


class RouteCreate(ORMModel):
    code: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, gt=0)
    stop_ids: list[UUID] = Field(default_factory=list)
    service_area: ServiceArea = ServiceArea.LPU
    service_types: list[TransportServiceType] = Field(
        default_factory=lambda: [TransportServiceType.CAMPUS_SHUTTLE]
    )
    verification_status: VerificationStatus = VerificationStatus.VERIFIED

    @field_validator("stop_ids")
    @classmethod
    def stop_ids_must_be_unique(cls, values: list[UUID]) -> list[UUID]:
        if len(values) != len(set(values)):
            raise ValueError("A stop can appear only once in a route.")
        return values

    @field_validator("service_types")
    @classmethod
    def service_types_must_be_unique(
        cls, values: list[TransportServiceType]
    ) -> list[TransportServiceType]:
        if not values:
            raise ValueError("At least one service type is required.")
        if len(values) != len(set(values)):
            raise ValueError("A service type can appear only once on a route.")
        return values


class RouteUpdate(ORMModel):
    code: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    stop_ids: list[UUID] | None = None
    service_area: ServiceArea | None = None
    service_types: list[TransportServiceType] | None = None
    verification_status: VerificationStatus | None = None

    @field_validator("code", "name")
    @classmethod
    def text_fields_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("This field cannot be null.")
        return value

    @field_validator("is_active", "service_area", "verification_status")
    @classmethod
    def active_flag_cannot_be_null(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("This field cannot be null.")
        return value

    @field_validator("stop_ids")
    @classmethod
    def stop_ids_must_be_unique(cls, values: list[UUID] | None) -> list[UUID] | None:
        if values is not None and len(values) != len(set(values)):
            raise ValueError("A stop can appear only once in a route.")
        return values

    @field_validator("service_types")
    @classmethod
    def service_types_must_be_unique(
        cls, values: list[TransportServiceType] | None
    ) -> list[TransportServiceType] | None:
        if values is not None and (
            not values or len(values) != len(set(values))
        ):
            raise ValueError("A route needs one or more unique service types.")
        return values


class StopSummary(ORMModel):
    id: UUID
    name: str
    is_active: bool
    service_area: ServiceArea


class RouteStopRead(ORMModel):
    stop_id: UUID
    position: int
    stop: StopSummary


class RouteRead(ORMModel):
    id: UUID
    code: str
    name: str
    estimated_duration_minutes: int | None
    service_area: ServiceArea
    service_types: list[TransportServiceType]
    verification_status: VerificationStatus
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
