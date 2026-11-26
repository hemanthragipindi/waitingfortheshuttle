import uuid

from pydantic import Field, field_validator

from app.core.enums import TransportServiceType, VerificationStatus
from app.schemas.common import ORMModel


class ShuttleCreate(ORMModel):
    vehicle_code: str = Field(min_length=1, max_length=32)
    capacity: int | None = Field(default=None, gt=0)
    route_id: uuid.UUID | None = None
    service_type: TransportServiceType = TransportServiceType.CAMPUS_SHUTTLE
    is_university_operated: bool = True
    verification_status: VerificationStatus = VerificationStatus.VERIFIED


class ShuttleUpdate(ORMModel):
    vehicle_code: str | None = Field(default=None, min_length=1, max_length=32)
    capacity: int | None = Field(default=None, gt=0)
    route_id: uuid.UUID | None = None
    service_type: TransportServiceType | None = None
    is_university_operated: bool | None = None
    verification_status: VerificationStatus | None = None
    is_active: bool | None = None

    @field_validator("vehicle_code")
    @classmethod
    def vehicle_code_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("vehicle_code cannot be null.")
        return value

    @field_validator(
        "is_active",
        "service_type",
        "is_university_operated",
        "verification_status",
    )
    @classmethod
    def optional_field_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null.")
        return value


class ShuttleRead(ORMModel):
    id: uuid.UUID
    vehicle_code: str
    capacity: int | None
    route_id: uuid.UUID | None
    service_type: TransportServiceType
    is_university_operated: bool
    verification_status: VerificationStatus
    is_active: bool
