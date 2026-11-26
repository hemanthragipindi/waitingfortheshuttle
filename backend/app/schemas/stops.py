from uuid import UUID

from pydantic import Field, field_validator

from app.core.enums import ServiceArea, VerificationStatus
from app.schemas.common import ORMModel


class StopCreate(ORMModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    service_area: ServiceArea = ServiceArea.LPU
    verification_status: VerificationStatus = VerificationStatus.VERIFIED


class StopUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    is_active: bool | None = None
    service_area: ServiceArea | None = None
    verification_status: VerificationStatus | None = None

    @field_validator("name")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("name cannot be null.")
        return value

    @field_validator("is_active", "service_area", "verification_status")
    @classmethod
    def optional_fields_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null.")
        return value


class StopRead(ORMModel):
    id: UUID
    name: str
    description: str | None
    service_area: ServiceArea
    verification_status: VerificationStatus
    is_active: bool
