from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class ShuttleServiceStatus(StrEnum):
    ON_TIME = "ON_TIME"
    DELAYED = "DELAYED"
    UNAVAILABLE = "UNAVAILABLE"
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
