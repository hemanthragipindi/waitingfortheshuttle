from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.stop import Stop
from app.models.user import User
from app.schemas.stops import StopCreate, StopUpdate


class DuplicateStopName(Exception):
    pass


def list_stops(
    db: Session,
    current_user: User,
    *,
    query: str | None,
    is_active: bool | None,
    skip: int,
    limit: int,
) -> tuple[list[Stop], int]:
    filters = []
    active_filter = True if current_user.role == UserRole.STUDENT.value else is_active
    if active_filter is not None:
        filters.append(Stop.is_active.is_(active_filter))
    if query:
        filters.append(Stop.name.ilike(f"%{query.strip()}%"))

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


def get_stop(db: Session, stop_id: UUID, current_user: User) -> Stop:
    stop = db.get(Stop, stop_id)
    if stop is None or (
        current_user.role == UserRole.STUDENT.value and not stop.is_active
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

    stop = Stop(name=name, description=payload.description)
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
