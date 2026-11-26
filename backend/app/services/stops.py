from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole, VerificationStatus
from app.models.stop import Stop
from app.models.user import User
from app.schemas.stops import StopCreate, StopUpdate


class DuplicateStopName(Exception):
    pass


def list_stops(
    db: Session,
    current_user: User | None,
    *,
    query: str | None,
    is_active: bool | None,
    service_area: str | None,
    verification_status: str | None,
    skip: int,
    limit: int,
) -> tuple[list[Stop], int]:
    filters = []
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    active_filter = is_active if is_admin else True
    if active_filter is not None:
        filters.append(Stop.is_active.is_(active_filter))
    if not is_admin:
        filters.append(Stop.verification_status == VerificationStatus.VERIFIED.value)
    elif verification_status:
        filters.append(Stop.verification_status == verification_status)
    if query:
        filters.append(Stop.name.ilike(f"%{query.strip()}%"))
    if service_area:
        filters.append(Stop.service_area == service_area)

    total = db.scalar(select(func.count(Stop.id)).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Stop)
            .where(*filters)
            .order_by(Stop.name, Stop.id)
            .offset(skip)
            .limit(limit)
        )
    )
    return items, total


def get_stop(db: Session, stop_id: UUID, current_user: User | None) -> Stop:
    stop = db.get(Stop, stop_id)
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    if stop is None or (
        not is_admin
        and (not stop.is_active or stop.verification_status != VerificationStatus.VERIFIED.value)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found.",
        )
    return stop


def get_stop_for_admin(db: Session, stop_id: UUID) -> Stop:
    stop = db.scalar(select(Stop).where(Stop.id == stop_id).with_for_update())
    if stop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop not found.",
        )
    return stop


def create_stop(db: Session, payload: StopCreate) -> Stop:
    name = payload.name.strip()
    if db.scalar(select(Stop.id).where(Stop.name == name)) is not None:
        raise DuplicateStopName

    stop = Stop(
        name=name,
        description=payload.description,
        service_area=payload.service_area.value,
        verification_status=payload.verification_status.value,
        is_active=payload.verification_status == VerificationStatus.VERIFIED,
    )
    db.add(stop)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if db.scalar(select(Stop.id).where(Stop.name == name)) is not None:
            raise DuplicateStopName from exc
        raise
    db.refresh(stop)
    return stop


def update_stop(db: Session, stop: Stop, payload: StopUpdate) -> Stop:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one stop field to update.",
        )

    name = updates.get("name")
    if "verification_status" in updates:
        updates["verification_status"] = updates["verification_status"].value
    if "service_area" in updates:
        updates["service_area"] = updates["service_area"].value
    if (
        updates.get("verification_status") is not None
        and updates["verification_status"] != VerificationStatus.VERIFIED.value
        and "is_active" not in updates
    ):
        updates["is_active"] = False
    if updates.get("is_active") is True and (
        updates.get("verification_status", stop.verification_status)
        != VerificationStatus.VERIFIED.value
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only verified stops can be activated.",
        )
    if name is not None:
        name = name.strip()
        existing = db.scalar(
            select(Stop.id).where(Stop.name == name, Stop.id != stop.id)
        )
        if existing is not None:
            raise DuplicateStopName
        updates["name"] = name

    for field, value in updates.items():
        setattr(stop, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if name is not None and db.scalar(
            select(Stop.id).where(Stop.name == name, Stop.id != stop.id)
        ) is not None:
            raise DuplicateStopName from exc
        raise
    db.refresh(stop)
    return stop
