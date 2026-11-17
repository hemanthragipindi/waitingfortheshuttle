from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user
from app.db.session import get_db_session
from app.models.stop import Stop
from app.models.user import User
from app.schemas.common import Page
from app.schemas.stops import StopCreate, StopRead, StopUpdate
from app.services.stops import (
    DuplicateStopName,
    create_stop,
    get_stop,
    get_stop_for_admin,
    list_stops,
    update_stop,
)

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("", response_model=Page[StopRead])
def read_stops(
    q: str | None = Query(default=None, min_length=1, max_length=120),
    is_active: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Page[StopRead]:
    items, total = list_stops(
        db,
        current_user,
        query=q,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return Page[StopRead](items=items, total=total, skip=skip, limit=limit)


@router.get("/{stop_id}", response_model=StopRead)
def read_stop(
    stop_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Stop:
    return get_stop(db, stop_id, current_user)


@router.post(
    "",
    response_model=StopRead,
    status_code=status.HTTP_201_CREATED,
)
def add_stop(
    payload: StopCreate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Stop:
    try:
        return create_stop(db, payload)
    except DuplicateStopName as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A stop with this name already exists.",
        ) from exc


@router.patch("/{stop_id}", response_model=StopRead)
def edit_stop(
    stop_id: UUID,
    payload: StopUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Stop:
    stop = get_stop_for_admin(db, stop_id)
    try:
        return update_stop(db, stop, payload)
    except DuplicateStopName as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A stop with this name already exists.",
        ) from exc
