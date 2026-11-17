from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.route import Route
from app.models.shuttle import Shuttle
from app.models.user import User
from app.schemas.shuttles import ShuttleCreate, ShuttleUpdate


class DuplicateVehicleCode(Exception):
    pass


def list_shuttles(
    db: Session,
    current_user: User,
    *,
    query: str | None,
    is_active: bool | None,
    route_id: UUID | None,
    skip: int,
    limit: int,
) -> tuple[list[Shuttle], int]:
    filters = []
    active_filter = True if current_user.role == UserRole.STUDENT.value else is_active
    if active_filter is not None:
        filters.append(Shuttle.is_active.is_(active_filter))
    if query and query.strip():
        filters.append(Shuttle.vehicle_code.ilike(f"%{query.strip()}%"))
    if route_id is not None:
        filters.append(Shuttle.route_id == route_id)

    total = db.scalar(select(func.count(Shuttle.id)).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Shuttle)
            .where(*filters)
            .order_by(Shuttle.vehicle_code, Shuttle.id)
            .offset(skip)
            .limit(limit)
        )
    )
    return items, total


def get_shuttle(db: Session, shuttle_id: UUID, current_user: User) -> Shuttle:
    shuttle = db.get(Shuttle, shuttle_id)
    if shuttle is None or (
        current_user.role == UserRole.STUDENT.value and not shuttle.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shuttle not found.",
        )
    return shuttle


def get_shuttle_for_admin(db: Session, shuttle_id: UUID) -> Shuttle:
    shuttle = db.scalar(
        select(Shuttle).where(Shuttle.id == shuttle_id).with_for_update()
    )
    if shuttle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shuttle not found.",
        )
    return shuttle


def _validate_route_assignment(db: Session, route_id: UUID | None) -> None:
    if route_id is None:
        return
    route = db.scalar(select(Route).where(Route.id == route_id).with_for_update())
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found.")
    if not route.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An inactive route cannot be assigned to a shuttle.",
        )


def create_shuttle(db: Session, payload: ShuttleCreate) -> Shuttle:
    if db.scalar(
        select(Shuttle.id).where(Shuttle.vehicle_code == payload.vehicle_code)
    ) is not None:
        raise DuplicateVehicleCode
    _validate_route_assignment(db, payload.route_id)
    shuttle = Shuttle(
        vehicle_code=payload.vehicle_code,
        capacity=payload.capacity,
        route_id=payload.route_id,
    )
    db.add(shuttle)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if db.scalar(
            select(Shuttle.id).where(Shuttle.vehicle_code == payload.vehicle_code)
        ) is not None:
            raise DuplicateVehicleCode from exc
        raise
    db.refresh(shuttle)
    return shuttle


def update_shuttle(db: Session, shuttle: Shuttle, payload: ShuttleUpdate) -> Shuttle:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one shuttle field to update.",
        )

    if "vehicle_code" in updates:
        existing = db.scalar(
            select(Shuttle.id).where(
                Shuttle.vehicle_code == updates["vehicle_code"],
                Shuttle.id != shuttle.id,
            )
        )
        if existing is not None:
            raise DuplicateVehicleCode
    if "route_id" in updates:
        _validate_route_assignment(db, updates["route_id"])

    for field, value in updates.items():
        setattr(shuttle, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        vehicle_code = updates.get("vehicle_code")
        if vehicle_code and db.scalar(
            select(Shuttle.id).where(
                Shuttle.vehicle_code == vehicle_code,
                Shuttle.id != shuttle.id,
            )
        ) is not None:
            raise DuplicateVehicleCode from exc
        raise
    db.refresh(shuttle)
    return shuttle
