from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.common import Page
from app.schemas.routes import (
    RouteCreate,
    RouteRead,
    RouteStopAdd,
    RouteStopOrder,
    RouteUpdate,
)
from app.services.routes import (
    DuplicateRouteCode,
    DuplicateRouteStop,
    add_route_stop,
    create_route,
    get_route,
    get_route_for_admin,
    list_routes,
    remove_route_stop,
    reorder_route_stops,
    update_route,
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=Page[RouteRead])
def read_routes(
    q: str | None = Query(default=None, min_length=1, max_length=120),
    is_active: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Page[RouteRead]:
    items, total = list_routes(
        db,
        current_user,
        query=q,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return Page[RouteRead](items=items, total=total, skip=skip, limit=limit)


@router.get("/{route_id}", response_model=RouteRead)
def read_route(
    route_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> RouteRead:
    return get_route(db, route_id, current_user)


@router.post(
    "",
    response_model=RouteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_route(
    payload: RouteCreate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> RouteRead:
    try:
        return create_route(db, payload)
    except DuplicateRouteCode as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A route with this code already exists.",
        ) from exc


@router.patch("/{route_id}", response_model=RouteRead)
def edit_route(
    route_id: UUID,
    payload: RouteUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> RouteRead:
    route = get_route_for_admin(db, route_id, for_update=True)
    try:
        return update_route(db, route, payload)
    except DuplicateRouteCode as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A route with this code already exists.",
        ) from exc


@router.post(
    "/{route_id}/stops",
    response_model=RouteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_stop_to_route(
    route_id: UUID,
    payload: RouteStopAdd,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> RouteRead:
    route = get_route_for_admin(db, route_id, for_update=True)
    try:
        return add_route_stop(db, route, payload)
    except DuplicateRouteStop as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stop is already assigned to the route.",
        ) from exc


@router.delete(
    "/{route_id}/stops/{stop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_stop_from_route(
    route_id: UUID,
    stop_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Response:
    route = get_route_for_admin(db, route_id, for_update=True)
    remove_route_stop(db, route, stop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{route_id}/stops/order", response_model=RouteRead)
def set_route_stop_order(
    route_id: UUID,
    payload: RouteStopOrder,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> RouteRead:
    route = get_route_for_admin(db, route_id, for_update=True)
    return reorder_route_stops(db, route, payload)
