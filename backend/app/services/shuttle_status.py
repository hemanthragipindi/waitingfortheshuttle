from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import ShuttleServiceStatus, UserRole, VerificationStatus
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
    current_user: User | None,
    *,
    lock: bool = False,
) -> Shuttle:
    query = select(Shuttle).where(Shuttle.id == shuttle_id)
    if lock:
        query = query.with_for_update()
    shuttle = db.scalar(query)
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    if shuttle is None or (
        not is_admin
        and (not shuttle.is_active or shuttle.verification_status != VerificationStatus.VERIFIED.value)
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
    current_user: User | None,
    route_id: UUID | None,
    service_area: str | None,
    service_type: str | None,
    status_filter: str | None,
    skip: int,
    limit: int,
) -> tuple[list[ShuttleStatusCurrentRead], int]:
    filters = []
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    if not is_admin:
        filters.append(Shuttle.is_active.is_(True))
        filters.append(Shuttle.verification_status == VerificationStatus.VERIFIED.value)
    if route_id is not None:
        filters.append(Shuttle.route_id == route_id)
    if service_area:
        filters.append(Shuttle.route.has(Route.service_area == service_area))
    if service_type:
        filters.append(Shuttle.service_type == service_type)
    if status_filter:
        latest_status = (
            select(
                ShuttleStatus.shuttle_id,
                ShuttleStatus.status,
                func.row_number()
                .over(
                    partition_by=ShuttleStatus.shuttle_id,
                    order_by=(
                        ShuttleStatus.created_at.desc(),
                        ShuttleStatus.id.desc(),
                    ),
                )
                .label("row_number"),
            )
            .subquery()
        )
        filters.append(
            Shuttle.id.in_(
                select(latest_status.c.shuttle_id).where(
                    latest_status.c.row_number == 1,
                    latest_status.c.status == status_filter,
                )
            )
        )

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
    current_user: User | None,
    *,
    skip: int,
    limit: int,
    service_area: str | None = None,
    service_type: str | None = None,
    status_filter: str | None = None,
) -> tuple[list[ShuttleStatusCurrentRead], int]:
    return _current_status_rows(
        db,
        current_user=current_user,
        route_id=None,
        service_area=service_area,
        service_type=service_type,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


def list_route_current_statuses(
    db: Session,
    route_id: UUID,
    current_user: User | None,
    *,
    skip: int,
    limit: int,
    service_area: str | None = None,
    service_type: str | None = None,
    status_filter: str | None = None,
) -> tuple[list[ShuttleStatusCurrentRead], int]:
    route = db.get(Route, route_id)
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    if route is None or (
        not is_admin
        and (not route.is_active or route.verification_status != VerificationStatus.VERIFIED.value)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return _current_status_rows(
        db,
        current_user=current_user,
        route_id=route_id,
        service_area=service_area,
        service_type=service_type,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


def get_current_status(
    db: Session,
    shuttle_id: UUID,
    current_user: User | None,
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
    current_user: User | None,
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
