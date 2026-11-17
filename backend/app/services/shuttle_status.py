from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import ShuttleServiceStatus, UserRole
from app.models.route import Route
from app.models.shuttle import Shuttle
from app.models.shuttle_status import ShuttleStatus
from app.models.user import User
from app.schemas.shuttle_status import (
    ShuttleStatusCreate,
    ShuttleStatusCurrentRead,
    ShuttleStatusRead,
)
from app.schemas.shuttles import ShuttleRead


def _get_shuttle_for_user(
    db: Session,
    shuttle_id: UUID,
    current_user: User,
    *,
    lock: bool = False,
) -> Shuttle:
    query = select(Shuttle).where(Shuttle.id == shuttle_id)
    if lock:
        query = query.with_for_update()
    shuttle = db.scalar(query)
    if shuttle is None or (
        current_user.role == UserRole.STUDENT.value and not shuttle.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shuttle not found.",
        )
    return shuttle


def _latest_status_query():
    return (
        select(
            ShuttleStatus.id.label("status_id"),
            ShuttleStatus.shuttle_id.label("shuttle_id"),
            func.row_number()
            .over(
                partition_by=ShuttleStatus.shuttle_id,
                order_by=(ShuttleStatus.created_at.desc(), ShuttleStatus.id.desc()),
            )
            .label("row_number"),
        )
        .subquery()
    )


def _current_status_read(
    shuttle: Shuttle,
    latest_status: ShuttleStatus | None,
) -> ShuttleStatusCurrentRead:
    return ShuttleStatusCurrentRead(
        shuttle=ShuttleRead.model_validate(shuttle),
        status_update_id=latest_status.id if latest_status else None,
        status=latest_status.status if latest_status else ShuttleServiceStatus.NOT_UPDATED,
        message=latest_status.message if latest_status else None,
        last_updated_at=latest_status.updated_at if latest_status else None,
    )


def _current_status_rows(
    db: Session,
    *,
    current_user: User,
    route_id: UUID | None,
    skip: int,
    limit: int,
) -> tuple[list[ShuttleStatusCurrentRead], int]:
    filters = []
    if current_user.role == UserRole.STUDENT.value:
        filters.append(Shuttle.is_active.is_(True))
    if route_id is not None:
        filters.append(Shuttle.route_id == route_id)

    total = db.scalar(select(func.count(Shuttle.id)).where(*filters)) or 0
    latest = _latest_status_query()
    rows = db.execute(
        select(Shuttle, ShuttleStatus)
        .outerjoin(
            latest,
            (latest.c.shuttle_id == Shuttle.id) & (latest.c.row_number == 1),
        )
        .outerjoin(ShuttleStatus, ShuttleStatus.id == latest.c.status_id)
        .where(*filters)
        .order_by(Shuttle.vehicle_code, Shuttle.id)
        .offset(skip)
        .limit(limit)
    ).all()
    items = [
        _current_status_read(shuttle, latest_status)
        for shuttle, latest_status in rows
    ]
    return items, total


def list_current_statuses(
    db: Session,
    current_user: User,
    *,
    skip: int,
    limit: int,
) -> tuple[list[ShuttleStatusCurrentRead], int]:
    return _current_status_rows(
        db,
        current_user=current_user,
        route_id=None,
        skip=skip,
        limit=limit,
    )


def list_route_current_statuses(
    db: Session,
    route_id: UUID,
    current_user: User,
    *,
    skip: int,
    limit: int,
) -> tuple[list[ShuttleStatusCurrentRead], int]:
    route = db.get(Route, route_id)
    if route is None or (
        current_user.role == UserRole.STUDENT.value and not route.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return _current_status_rows(
        db,
        current_user=current_user,
        route_id=route_id,
        skip=skip,
        limit=limit,
    )


def get_current_status(
    db: Session,
    shuttle_id: UUID,
    current_user: User,
) -> ShuttleStatusCurrentRead:
    shuttle = _get_shuttle_for_user(db, shuttle_id, current_user)
    latest_status = db.scalar(
        select(ShuttleStatus)
        .where(ShuttleStatus.shuttle_id == shuttle_id)
        .order_by(ShuttleStatus.created_at.desc(), ShuttleStatus.id.desc())
        .limit(1)
    )
    return _current_status_read(shuttle, latest_status)


def list_status_history(
    db: Session,
    shuttle_id: UUID,
    current_user: User,
    *,
    skip: int,
    limit: int,
) -> tuple[list[ShuttleStatus], int]:
    _get_shuttle_for_user(db, shuttle_id, current_user)
    total = (
        db.scalar(
            select(func.count(ShuttleStatus.id)).where(
                ShuttleStatus.shuttle_id == shuttle_id
            )
        )
        or 0
    )
    history = list(
        db.scalars(
            select(ShuttleStatus)
            .options(joinedload(ShuttleStatus.shuttle))
            .where(ShuttleStatus.shuttle_id == shuttle_id)
            .order_by(ShuttleStatus.created_at.desc(), ShuttleStatus.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )
    return history, total


def create_status_update(
    db: Session,
    payload: ShuttleStatusCreate,
    current_admin: User,
) -> ShuttleStatus:
    shuttle = _get_shuttle_for_user(
        db,
        payload.shuttle_id,
        current_admin,
        lock=True,
    )
    # PostgreSQL now() is transaction-scoped, so capture the time after the row lock.
    recorded_at = (
        db.scalar(select(func.clock_timestamp()))
        if db.get_bind().dialect.name == "postgresql"
        else datetime.now(UTC)
    )
    status_update = ShuttleStatus(
        shuttle_id=shuttle.id,
        status=payload.status.value,
        message=payload.message,
        updated_by_id=current_admin.id,
        created_at=recorded_at,
        updated_at=recorded_at,
    )
    db.add(status_update)
    db.commit()
    db.refresh(status_update)
    return status_update
