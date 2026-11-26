from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_optional_current_user
from app.core.enums import ServiceArea, ShuttleServiceStatus, TransportServiceType
from app.db.session import get_db_session
from app.models.shuttle_status import ShuttleStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.shuttle_status import (
    ShuttleStatusCreate,
    ShuttleStatusCurrentRead,
    ShuttleStatusRead,
)
from app.services.shuttle_status import (
    create_status_update,
    get_current_status,
    list_current_statuses,
    list_route_current_statuses,
    list_status_history,
)

router = APIRouter(prefix="/shuttle-status", tags=["shuttle status"])


@router.get("", response_model=Page[ShuttleStatusCurrentRead])
def read_current_statuses(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    service_area: ServiceArea | None = None,
    service_type: TransportServiceType | None = None,
    status_filter: ShuttleServiceStatus | None = Query(default=None, alias="status"),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
) -> Page[ShuttleStatusCurrentRead]:
    items, total = list_current_statuses(
        db,
        current_user,
        skip=skip,
        limit=limit,
        service_area=service_area.value if service_area else None,
        service_type=service_type.value if service_type else None,
        status_filter=status_filter.value if status_filter else None,
    )
    return Page[ShuttleStatusCurrentRead](
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/route/{route_id}", response_model=Page[ShuttleStatusCurrentRead])
def read_route_current_statuses(
    route_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    service_area: ServiceArea | None = None,
    service_type: TransportServiceType | None = None,
    status_filter: ShuttleServiceStatus | None = Query(default=None, alias="status"),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
) -> Page[ShuttleStatusCurrentRead]:
    items, total = list_route_current_statuses(
        db,
        route_id,
        current_user,
        skip=skip,
        limit=limit,
        service_area=service_area.value if service_area else None,
        service_type=service_type.value if service_type else None,
        status_filter=status_filter.value if status_filter else None,
    )
    return Page[ShuttleStatusCurrentRead](
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/shuttle/{shuttle_id}", response_model=ShuttleStatusCurrentRead)
def read_shuttle_current_status(
    shuttle_id: UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
) -> ShuttleStatusCurrentRead:
    return get_current_status(db, shuttle_id, current_user)


@router.get(
    "/shuttle/{shuttle_id}/history",
    response_model=Page[ShuttleStatusRead],
)
def read_shuttle_status_history(
    shuttle_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
) -> Page[ShuttleStatusRead]:
    items, total = list_status_history(
        db,
        shuttle_id,
        current_user,
        skip=skip,
        limit=limit,
    )
    return Page[ShuttleStatusRead](items=items, total=total, skip=skip, limit=limit)


@router.post(
    "",
    response_model=ShuttleStatusRead,
    status_code=status.HTTP_201_CREATED,
)
def add_shuttle_status(
    payload: ShuttleStatusCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> ShuttleStatus:
    return create_status_update(db, payload, current_admin)
