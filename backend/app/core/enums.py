from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class ServiceArea(StrEnum):
    LPU = "LPU"
    PHAGWARA = "PHAGWARA"
    JALANDHAR = "JALANDHAR"


class TransportServiceType(StrEnum):
    CAMPUS_SHUTTLE = "CAMPUS_SHUTTLE"
    E_RICKSHAW = "E_RICKSHAW"
    AUTO_RICKSHAW = "AUTO_RICKSHAW"
    PUBLIC_BUS = "PUBLIC_BUS"
    TRAIN = "TRAIN"
    OTHER = "OTHER"


class VerificationStatus(StrEnum):
    PLANNED = "PLANNED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"


class ShuttleServiceStatus(StrEnum):
    ON_TIME = "ON_TIME"
    DELAYED = "DELAYED"
    UNAVAILABLE = "UNAVAILABLE"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"
    NOT_UPDATED = "NOT_UPDATED"


class FeedbackCategory(StrEnum):
    DELAY = "DELAY"
    OVERCROWDING = "OVERCROWDING"
    INCORRECT_STOP = "INCORRECT_STOP"
    SUGGESTION = "SUGGESTION"
    OTHER = "OTHER"


class FeedbackStatus(StrEnum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
