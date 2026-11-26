import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.core.enums import ShuttleServiceStatus
from app.db.base import Base
from app.models import (
    Feedback,
    Route,
    RouteServiceType,
    RouteStop,
    Shuttle,
    ShuttleStatus,
    Stop,
    User,
)
from app.schemas.announcements import AnnouncementCreate
from app.schemas.routes import RouteCreate
from app.schemas.shuttle_status import ShuttleStatusCreate


@pytest.fixture
def test_engine():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_all_models_and_relationships_are_registered(test_engine) -> None:
    configure_mappers()
    assert set(Base.metadata.tables) == {
        "users",
        "stops",
        "routes",
        "route_stops",
        "route_service_types",
        "shuttles",
        "shuttle_status",
        "announcements",
        "feedback",
    }

    with Session(test_engine) as session:
        student = User(
            email="test-only-student@example.invalid",
            full_name="TEST ONLY Student",
            password_hash="test-only-hash",
        )
        first_stop = Stop(name="TEST ONLY First Stop")
        second_stop = Stop(name="TEST ONLY Second Stop")
        route = Route(code="TEST-ONLY-1", name="TEST ONLY Route")
        route.service_types = [
            RouteServiceType(service_type="CAMPUS_SHUTTLE"),
            RouteServiceType(service_type="PUBLIC_BUS"),
        ]
        shuttle = Shuttle(vehicle_code="TEST-ONLY-VEHICLE", capacity=20, route=route)
        route.route_stops = [
            RouteStop(stop=first_stop, position=1),
            RouteStop(stop=second_stop, position=2),
        ]
        session.add_all(
            [
                student,
                first_stop,
                second_stop,
                route,
                shuttle,
                ShuttleStatus(shuttle=shuttle, status="ON_TIME", updated_by=student),
                Feedback(
                    submitted_by=student,
                    category="SUGGESTION",
                    message="TEST ONLY feedback",
                    route=route,
                ),
            ]
        )
        session.commit()

        loaded_route = session.scalar(select(Route).where(Route.code == "TEST-ONLY-1"))
        assert loaded_route is not None
        assert [item.stop.name for item in loaded_route.route_stops] == [
            "TEST ONLY First Stop",
            "TEST ONLY Second Stop",
        ]
        assert loaded_route.shuttles[0].status_updates[0].status == "ON_TIME"
        assert [item.service_type for item in loaded_route.service_types] == [
            "CAMPUS_SHUTTLE",
            "PUBLIC_BUS",
        ]


def test_route_stop_order_and_status_checks_reject_invalid_values(test_engine) -> None:
    with Session(test_engine) as session:
        first_stop = Stop(name="TEST ONLY Constraint Stop A")
        second_stop = Stop(name="TEST ONLY Constraint Stop B")
        route = Route(
            code="TEST-ONLY-CONSTRAINT",
            name="TEST ONLY Constraint Route",
            route_stops=[
                RouteStop(stop=first_stop, position=1),
                RouteStop(stop=second_stop, position=1),
            ],
        )
        session.add(route)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        shuttle = Shuttle(vehicle_code="TEST-ONLY-CONSTRAINT-VEHICLE", capacity=10)
        session.add(shuttle)
        session.flush()
        session.add(ShuttleStatus(shuttle=shuttle, status="ARRIVING"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_request_schemas_validate_order_status_and_announcement_dates() -> None:
    stop_id = "00000000-0000-0000-0000-000000000001"

    with pytest.raises(ValueError, match="only once"):
        RouteCreate(code="TEST-ONLY", name="TEST ONLY route", stop_ids=[stop_id, stop_id])

    update = ShuttleStatusCreate(
        shuttle_id="00000000-0000-0000-0000-000000000002",
        status=ShuttleServiceStatus.DELAYED,
    )
    assert update.status is ShuttleServiceStatus.DELAYED

    with pytest.raises(ValueError, match="ends_at"):
        AnnouncementCreate(
            title="TEST ONLY notice",
            body="TEST ONLY message",
            starts_at="2026-01-02T10:00:00Z",
            ends_at="2026-01-01T10:00:00Z",
        )
