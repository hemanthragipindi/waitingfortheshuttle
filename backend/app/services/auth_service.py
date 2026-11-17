from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import StudentRegistration


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


def register_student(db: Session, registration: StudentRegistration) -> User:
    email = str(registration.email).casefold()
    user = User(
        email=email,
        full_name=registration.full_name,
        password_hash=hash_password(registration.password),
        role=UserRole.STUDENT.value,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing_user = db.scalar(select(User.id).where(User.email == email))
        if existing_user is not None:
            raise EmailAlreadyRegistered from exc
        raise
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
    expected_role: UserRole,
) -> User:
    normalized_email = email.casefold()
    user = db.scalar(select(User).where(User.email == normalized_email))
    password_matches = user is not None and verify_password(password, user.password_hash)
    if (
        user is None
        or not password_matches
        or not user.is_active
        or user.role != expected_role.value
    ):
        raise InvalidCredentials
    return user
