from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user
from app.db.session import get_db_session
from app.models.shuttle import Shuttle
from app.models.user import User
from app.schemas.common import Page
from app.schemas.shuttles import ShuttleCreate, ShuttleRead, ShuttleUpdate
from app.services.shuttles import (
    DuplicateVehicleCode,
    create_shuttle,
    get_shuttle,
    get_shuttle_for_admin,
    list_shuttles,
    update_shuttle,
)

router = APIRouter(prefix="/shuttles", tags=["shuttles"])


@router.get("", response_model=Page[ShuttleRead])
def read_shuttles(
    q: str | None = Query(default=None, min_length=1, max_length=32),
    is_active: bool | None = None,
    route_id: UUID | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Page[ShuttleRead]:
    items, total = list_shuttles(
        db,
        current_user,
        query=q,
        is_active=is_active,
        route_id=route_id,
        skip=skip,
        limit=limit,
    )
    return Page[ShuttleRead](items=items, total=total, skip=skip, limit=limit)


@router.get("/{shuttle_id}", response_model=ShuttleRead)
def read_shuttle(
    shuttle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Shuttle:
    return get_shuttle(db, shuttle_id, current_user)


@router.post(
    "",
    response_model=ShuttleRead,
    status_code=status.HTTP_201_CREATED,
)
def add_shuttle(
    payload: ShuttleCreate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Shuttle:
    try:
        return create_shuttle(db, payload)
    except DuplicateVehicleCode as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A shuttle with this vehicle code already exists.",
        ) from exc


@router.patch("/{shuttle_id}", response_model=ShuttleRead)
def edit_shuttle(
    shuttle_id: UUID,
    payload: ShuttleUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Shuttle:
    shuttle = get_shuttle_for_admin(db, shuttle_id)
    try:
        return update_shuttle(db, shuttle, payload)
    except DuplicateVehicleCode as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A shuttle with this vehicle code already exists.",
        ) from exc
