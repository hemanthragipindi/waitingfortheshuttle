from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload

from app.core.enums import UserRole, VerificationStatus
from app.models.route import Route
from app.models.route_service_type import RouteServiceType
from app.models.route_stop import RouteStop
from app.models.shuttle import Shuttle
from app.models.shuttle_status import ShuttleStatus
from app.models.stop import Stop
from app.models.user import User
from app.schemas.routes import (
    RouteCreate,
    RouteRead,
    RouteStopAdd,
    RouteStopOrder,
    RouteUpdate,
)


class DuplicateRouteCode(Exception):
    pass


class DuplicateRouteStop(Exception):
    pass


def _route_query():
    return select(Route).options(
        selectinload(Route.route_stops).selectinload(RouteStop.stop),
        selectinload(Route.service_types),
    )


def _route_response(route: Route, include_inactive_stops: bool) -> RouteRead:
    route_data = {
        "id": route.id,
        "code": route.code,
        "name": route.name,
        "estimated_duration_minutes": route.estimated_duration_minutes,
        "service_area": route.service_area,
        "service_types": [item.service_type for item in route.service_types],
        "verification_status": route.verification_status,
        "is_active": route.is_active,
        "route_stops": [
            association
            for association in route.route_stops
            if include_inactive_stops or association.stop.is_active
        ],
    }
    return RouteRead.model_validate(route_data)


def _load_route_stops(db: Session, stop_ids: list[UUID]) -> list[Stop]:
    if not stop_ids:
        return []
    stops = list(
        db.scalars(
            select(Stop).where(Stop.id.in_(stop_ids)).with_for_update()
        )
    )
    stops_by_id = {stop.id: stop for stop in stops}
    missing_ids = [stop_id for stop_id in stop_ids if stop_id not in stops_by_id]
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stop not found: {missing_ids[0]}",
        )
    inactive_stops = [stop for stop in stops if not stop.is_active]
    if inactive_stops:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inactive stop cannot be assigned: {inactive_stops[0].id}",
        )
    return [stops_by_id[stop_id] for stop_id in stop_ids]


def _replace_route_stops(db: Session, route: Route, stops: list[Stop]) -> None:
    route.route_stops.clear()
    db.flush()
    route.route_stops.extend(
        RouteStop(stop=stop, position=position)
        for position, stop in enumerate(stops, start=1)
    )
    db.flush()


def list_routes(
    db: Session,
    current_user: User | None,
    *,
    query: str | None,
    is_active: bool | None,
    service_area: str | None,
    service_type: str | None,
    destination: str | None,
    status_filter: str | None,
    skip: int,
    limit: int,
) -> tuple[list[RouteRead], int]:
    filters = []
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    active_filter = is_active if is_admin else True
    if active_filter is not None:
        filters.append(Route.is_active.is_(active_filter))
    if not is_admin:
        filters.append(Route.verification_status == VerificationStatus.VERIFIED.value)
    if query and query.strip():
        pattern = f"%{query.strip()}%"
        filters.append(Route.name.ilike(pattern) | Route.code.ilike(pattern))
    if service_area:
        filters.append(Route.service_area == service_area)
    if service_type:
        filters.append(
            Route.service_types.any(RouteServiceType.service_type == service_type)
        )
    if destination:
        destination_pattern = f"%{destination.strip()}%"
        last_stop = aliased(RouteStop)
        last_position = (
            select(func.max(last_stop.position))
            .where(last_stop.route_id == Route.id)
            .scalar_subquery()
        )
        filters.append(
            Route.route_stops.any(
                (RouteStop.position == last_position)
                & RouteStop.stop.has(Stop.name.ilike(destination_pattern))
            )
        )
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
            Route.shuttles.any(
                Shuttle.id.in_(
                    select(latest_status.c.shuttle_id).where(
                        latest_status.c.row_number == 1,
                        latest_status.c.status == status_filter,
                    )
                )
            )
        )

    total = db.scalar(select(func.count(Route.id)).where(*filters)) or 0
    routes = list(
        db.scalars(
            _route_query()
            .where(*filters)
            .order_by(Route.name, Route.id)
            .offset(skip)
            .limit(limit)
        )
    )
    include_inactive_stops = current_user is not None and current_user.role == UserRole.ADMIN.value
    return [
        _route_response(route, include_inactive_stops) for route in routes
    ], total


def get_route(db: Session, route_id: UUID, current_user: User | None) -> RouteRead:
    route = db.scalar(_route_query().where(Route.id == route_id))
    is_admin = current_user is not None and current_user.role == UserRole.ADMIN.value
    if route is None or (
        not is_admin
        and (not route.is_active or route.verification_status != VerificationStatus.VERIFIED.value)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return _route_response(route, is_admin)


def get_route_for_admin(
    db: Session,
    route_id: UUID,
    *,
    for_update: bool = False,
) -> Route:
    statement = _route_query().where(Route.id == route_id)
    if for_update:
        statement = statement.with_for_update()
    route = db.scalar(statement)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )
    return route


def _ensure_unique_code(db: Session, code: str, route_id: UUID | None = None) -> None:
    statement = select(Route.id).where(Route.code == code)
    if route_id is not None:
        statement = statement.where(Route.id != route_id)
    if db.scalar(statement) is not None:
        raise DuplicateRouteCode


def create_route(db: Session, payload: RouteCreate) -> RouteRead:
    _ensure_unique_code(db, payload.code)
    stops = _load_route_stops(db, payload.stop_ids)
    route = Route(
        code=payload.code,
        name=payload.name,
        estimated_duration_minutes=payload.estimated_duration_minutes,
        service_area=payload.service_area.value,
        verification_status=payload.verification_status.value,
        route_stops=[
            RouteStop(stop=stop, position=position)
            for position, stop in enumerate(stops, start=1)
        ],
        service_types=[
            RouteServiceType(service_type=service_type.value)
            for service_type in payload.service_types
        ],
    )
    db.add(route)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if db.scalar(select(Route.id).where(Route.code == payload.code)) is not None:
            raise DuplicateRouteCode from exc
        raise
    route = get_route_for_admin(db, route.id)
    return _route_response(route, include_inactive_stops=True)


def update_route(db: Session, route: Route, payload: RouteUpdate) -> RouteRead:
    updates = payload.model_dump(exclude_unset=True)
    stop_ids = updates.pop("stop_ids", None)
    service_types = updates.pop("service_types", None)
    if "stop_ids" in payload.model_fields_set and stop_ids is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="stop_ids must be a list; use an empty list to remove all stops.",
        )
    if not updates and stop_ids is None and service_types is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one route field to update.",
        )
    if "code" in updates:
        _ensure_unique_code(db, updates["code"], route.id)
    if "service_area" in updates:
        updates["service_area"] = updates["service_area"].value
    if "verification_status" in updates:
        updates["verification_status"] = updates["verification_status"].value
    if (
        updates.get("verification_status") is not None
        and updates["verification_status"] != "VERIFIED"
        and "is_active" not in updates
    ):
        updates["is_active"] = False
    if updates.get("is_active") is True and (
        updates.get("verification_status", route.verification_status)
        != "VERIFIED"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only verified routes can be activated.",
        )

    stops = _load_route_stops(db, stop_ids) if stop_ids is not None else None
    for field, value in updates.items():
        setattr(route, field, value)
    if stops is not None:
        _replace_route_stops(db, route, stops)
    if service_types is not None:
        route.service_types.clear()
        route.service_types.extend(
            RouteServiceType(service_type=service_type.value)
            for service_type in service_types
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        code = updates.get("code")
        if code and db.scalar(
            select(Route.id).where(Route.code == code, Route.id != route.id)
        ) is not None:
            raise DuplicateRouteCode from exc
        raise
    return _route_response(get_route_for_admin(db, route.id), include_inactive_stops=True)


def add_route_stop(
    db: Session,
    route: Route,
    payload: RouteStopAdd,
) -> RouteRead:
    stop = db.get(Stop, payload.stop_id)
    if stop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found.")
    if not stop.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inactive stops cannot be assigned to a route.",
        )

    current_stops = [association.stop for association in route.route_stops]
    if any(existing.id == stop.id for existing in current_stops):
        raise DuplicateRouteStop
    position = payload.position or len(current_stops) + 1
    if position > len(current_stops) + 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Position must be between 1 and the next available position.",
        )
    current_stops.insert(position - 1, stop)
    _replace_route_stops(db, route, current_stops)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if db.scalar(
            select(RouteStop.id).where(
                RouteStop.route_id == route.id,
                RouteStop.stop_id == stop.id,
            )
        ) is not None:
            raise DuplicateRouteStop from exc
        raise
    return _route_response(get_route_for_admin(db, route.id), include_inactive_stops=True)


def remove_route_stop(db: Session, route: Route, stop_id: UUID) -> None:
    current_stops = [association.stop for association in route.route_stops]
    updated_stops = [stop for stop in current_stops if stop.id != stop_id]
    if len(updated_stops) == len(current_stops):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stop is not assigned to this route.",
        )
    _replace_route_stops(db, route, updated_stops)
    db.commit()


def reorder_route_stops(
    db: Session,
    route: Route,
    payload: RouteStopOrder,
) -> RouteRead:
    current_ids = [association.stop_id for association in route.route_stops]
    if set(current_ids) != set(payload.stop_ids) or len(current_ids) != len(payload.stop_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="stop_ids must contain every assigned stop exactly once.",
        )
    stops_by_id = {association.stop_id: association.stop for association in route.route_stops}
    _replace_route_stops(db, route, [stops_by_id[stop_id] for stop_id in payload.stop_ids])
    db.commit()
    return _route_response(get_route_for_admin(db, route.id), include_inactive_stops=True)
