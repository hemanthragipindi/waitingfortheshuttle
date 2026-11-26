from collections.abc import Generator

import httpx
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.user import User

API_PREFIX = "/api/v1"
ADMIN_EMAIL = "transport-admin-test@example.com"
ADMIN_PASSWORD = "test-only-admin-password"
STUDENT_EMAIL = "transport-student-test@example.com"
STUDENT_PASSWORD = "test-only-student-password"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def transport_engine(monkeypatch: pytest.MonkeyPatch) -> Generator:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-signing-secret-with-48-characters")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db
    with Session(engine) as session:
        session.add_all(
            [
                User(
                    email=ADMIN_EMAIL,
                    full_name="TEST ONLY Transport Admin",
                    password_hash=hash_password(ADMIN_PASSWORD),
                    role=UserRole.ADMIN.value,
                ),
                User(
                    email=STUDENT_EMAIL,
                    full_name="TEST ONLY Transport Student",
                    password_hash=hash_password(STUDENT_PASSWORD),
                    role=UserRole.STUDENT.value,
                ),
            ]
        )
        session.commit()

    yield engine
    app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
async def transport_client(transport_engine):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


def csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    return {
        "Origin": "http://127.0.0.1:5173",
        "X-CSRF-Token": client.cookies.get("p05_csrf_token"),
    }


@pytest.mark.anyio
async def test_stops_routes_shuttles_and_student_admin_permissions(
    transport_client: httpx.AsyncClient,
) -> None:
    client = transport_client
    admin_login = await client.post(
        f"{API_PREFIX}/auth/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert admin_login.status_code == 200
    admin_headers = csrf_headers(client)

    stop_a = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY North Gate", "description": "TEST ONLY stop"},
        headers=admin_headers,
    )
    stop_b = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY Library", "description": "TEST ONLY stop"},
        headers=admin_headers,
    )
    stop_c = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY East Hall", "description": None},
        headers=admin_headers,
    )
    assert [stop.status_code for stop in (stop_a, stop_b, stop_c)] == [201, 201, 201]
    stop_a_data, stop_b_data, stop_c_data = (
        stop_a.json(),
        stop_b.json(),
        stop_c.json(),
    )

    duplicate_stop = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY North Gate"},
        headers=admin_headers,
    )
    assert duplicate_stop.status_code == 409

    stop_search = await client.get(
        f"{API_PREFIX}/stops",
        params={"q": "North", "skip": 0, "limit": 1},
    )
    assert stop_search.status_code == 200
    assert stop_search.json()["total"] == 1
    assert stop_search.json()["items"][0]["id"] == stop_a_data["id"]

    stop_patch = await client.patch(
        f"{API_PREFIX}/stops/{stop_a_data['id']}",
        json={"name": "TEST ONLY North Entrance"},
        headers=admin_headers,
    )
    assert stop_patch.status_code == 200
    assert stop_patch.json()["name"] == "TEST ONLY North Entrance"

    route_response = await client.post(
        f"{API_PREFIX}/routes",
        json={
            "code": "TEST-ROUTE-01",
            "name": "TEST ONLY North Loop",
            "estimated_duration_minutes": 15,
            "stop_ids": [stop_a_data["id"], stop_b_data["id"]],
        },
        headers=admin_headers,
    )
    assert route_response.status_code == 201
    route_data = route_response.json()
    route_id = route_data["id"]
    assert [item["position"] for item in route_data["route_stops"]] == [1, 2]

    duplicate_route = await client.post(
        f"{API_PREFIX}/routes",
        json={"code": "TEST-ROUTE-01", "name": "TEST ONLY duplicate"},
        headers=admin_headers,
    )
    assert duplicate_route.status_code == 409

    missing_stop_route = await client.post(
        f"{API_PREFIX}/routes",
        json={
            "code": "TEST-ROUTE-MISSING",
            "name": "TEST ONLY invalid stop",
            "stop_ids": ["00000000-0000-0000-0000-000000000001"],
        },
        headers=admin_headers,
    )
    assert missing_stop_route.status_code == 404

    duplicate_assignment = await client.post(
        f"{API_PREFIX}/routes/{route_id}/stops",
        json={"stop_id": stop_a_data["id"]},
        headers=admin_headers,
    )
    assert duplicate_assignment.status_code == 409

    add_stop = await client.post(
        f"{API_PREFIX}/routes/{route_id}/stops",
        json={"stop_id": stop_c_data["id"], "position": 2},
        headers=admin_headers,
    )
    assert add_stop.status_code == 201
    assert [item["stop_id"] for item in add_stop.json()["route_stops"]] == [
        stop_a_data["id"],
        stop_c_data["id"],
        stop_b_data["id"],
    ]

    duplicate_order = await client.put(
        f"{API_PREFIX}/routes/{route_id}/stops/order",
        json={"stop_ids": [stop_a_data["id"], stop_a_data["id"], stop_b_data["id"]]},
        headers=admin_headers,
    )
    assert duplicate_order.status_code == 422

    reordered = await client.put(
        f"{API_PREFIX}/routes/{route_id}/stops/order",
        json={"stop_ids": [stop_b_data["id"], stop_a_data["id"], stop_c_data["id"]]},
        headers=admin_headers,
    )
    assert reordered.status_code == 200
    assert [item["position"] for item in reordered.json()["route_stops"]] == [1, 2, 3]
    assert [item["stop_id"] for item in reordered.json()["route_stops"]] == [
        stop_b_data["id"],
        stop_a_data["id"],
        stop_c_data["id"],
    ]

    removed = await client.delete(
        f"{API_PREFIX}/routes/{route_id}/stops/{stop_c_data['id']}",
        headers=admin_headers,
    )
    assert removed.status_code == 204
    detail_after_remove = await client.get(f"{API_PREFIX}/routes/{route_id}")
    assert [item["position"] for item in detail_after_remove.json()["route_stops"]] == [1, 2]

    route_update = await client.patch(
        f"{API_PREFIX}/routes/{route_id}",
        json={
            "name": "TEST ONLY North Loop Revised",
            "estimated_duration_minutes": 20,
        },
        headers=admin_headers,
    )
    assert route_update.status_code == 200
    assert route_update.json()["name"] == "TEST ONLY North Loop Revised"
    assert route_update.json()["estimated_duration_minutes"] == 20

    shuttle = await client.post(
        f"{API_PREFIX}/shuttles",
        json={
            "vehicle_code": "TEST-VEHICLE-01",
            "capacity": 24,
            "route_id": route_id,
        },
        headers=admin_headers,
    )
    assert shuttle.status_code == 201
    shuttle_id = shuttle.json()["id"]

    duplicate_shuttle = await client.post(
        f"{API_PREFIX}/shuttles",
        json={"vehicle_code": "TEST-VEHICLE-01", "capacity": 12},
        headers=admin_headers,
    )
    assert duplicate_shuttle.status_code == 409

    missing_route_shuttle = await client.post(
        f"{API_PREFIX}/shuttles",
        json={
            "vehicle_code": "TEST-VEHICLE-MISSING",
            "capacity": 12,
            "route_id": "00000000-0000-0000-0000-000000000001",
        },
        headers=admin_headers,
    )
    assert missing_route_shuttle.status_code == 404

    shuttle_patch = await client.patch(
        f"{API_PREFIX}/shuttles/{shuttle_id}",
        json={"capacity": 30},
        headers=admin_headers,
    )
    assert shuttle_patch.status_code == 200
    assert shuttle_patch.json()["capacity"] == 30

    inactive_stop = await client.patch(
        f"{API_PREFIX}/stops/{stop_b_data['id']}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert inactive_stop.status_code == 200

    inactive_route = await client.post(
        f"{API_PREFIX}/routes",
        json={"code": "TEST-ROUTE-INACTIVE", "name": "TEST ONLY inactive"},
        headers=admin_headers,
    )
    assert inactive_route.status_code == 201
    inactive_route_id = inactive_route.json()["id"]
    route_patch = await client.patch(
        f"{API_PREFIX}/routes/{inactive_route_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert route_patch.status_code == 200

    client.cookies.clear()
    student_login = await client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD},
    )
    assert student_login.status_code == 200
    student_headers = csrf_headers(client)

    active_stops = await client.get(f"{API_PREFIX}/stops")
    assert active_stops.status_code == 200
    assert all(item["is_active"] for item in active_stops.json()["items"])
    assert active_stops.json()["total"] == 2
    assert (
        await client.get(f"{API_PREFIX}/stops/{stop_b_data['id']}")
    ).status_code == 404

    active_routes = await client.get(f"{API_PREFIX}/routes")
    assert active_routes.status_code == 200
    assert all(item["is_active"] for item in active_routes.json()["items"])
    student_route = await client.get(f"{API_PREFIX}/routes/{route_id}")
    assert student_route.status_code == 200
    assert all(item["stop"]["is_active"] for item in student_route.json()["route_stops"])
    assert (await client.get(f"{API_PREFIX}/routes/{inactive_route_id}")).status_code == 404

    active_shuttles = await client.get(f"{API_PREFIX}/shuttles")
    assert active_shuttles.status_code == 200
    assert active_shuttles.json()["total"] == 1

    student_stop_create = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY Student Stop"},
        headers=student_headers,
    )
    student_route_create = await client.post(
        f"{API_PREFIX}/routes",
        json={"code": "STUDENT-ROUTE", "name": "TEST ONLY denied"},
        headers=student_headers,
    )
    student_shuttle_update = await client.patch(
        f"{API_PREFIX}/shuttles/{shuttle_id}",
        json={"capacity": 1},
        headers=student_headers,
    )
    assert student_stop_create.status_code == 403
    assert student_route_create.status_code == 403
    assert student_shuttle_update.status_code == 403

    missing_id = "00000000-0000-0000-0000-000000000001"
    assert (await client.get(f"{API_PREFIX}/stops/{missing_id}")).status_code == 404
    assert (await client.get(f"{API_PREFIX}/routes/{missing_id}")).status_code == 404
    assert (await client.get(f"{API_PREFIX}/shuttles/{missing_id}")).status_code == 404


@pytest.mark.anyio
async def test_public_unauthenticated_read_only_and_authorization_guards(
    transport_client: httpx.AsyncClient,
) -> None:
    client = transport_client
    admin_login = await client.post(
        f"{API_PREFIX}/auth/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert admin_login.status_code == 200
    headers = csrf_headers(client)

    verified_stop = await client.post(
        f"{API_PREFIX}/stops",
        json={
            "name": "PUBLIC-VERIFIED-STOP",
            "service_area": "LPU",
            "verification_status": "VERIFIED",
        },
        headers=headers,
    )
    assert verified_stop.status_code == 201
    verified_stop_id = verified_stop.json()["id"]

    unverified_stop = await client.post(
        f"{API_PREFIX}/stops",
        json={
            "name": "PUBLIC-UNVERIFIED-STOP",
            "service_area": "LPU",
            "verification_status": "PENDING_VERIFICATION",
        },
        headers=headers,
    )
    assert unverified_stop.status_code == 201
    unverified_stop_id = unverified_stop.json()["id"]

    # Clear all cookies to simulate an unauthenticated public visitor
    client.cookies.clear()

    # 1. Public can view active verified stops
    public_stops = await client.get(f"{API_PREFIX}/stops")
    assert public_stops.status_code == 200
    stop_ids = [item["id"] for item in public_stops.json()["items"]]
    assert verified_stop_id in stop_ids
    assert unverified_stop_id not in stop_ids

    # 2. Public can view specific verified stop, but unverified/inactive returns 404
    assert (await client.get(f"{API_PREFIX}/stops/{verified_stop_id}")).status_code == 200
    assert (await client.get(f"{API_PREFIX}/stops/{unverified_stop_id}")).status_code == 404

    # 3. Public can view routes, shuttles, status, announcements without login
    assert (await client.get(f"{API_PREFIX}/routes")).status_code == 200
    assert (await client.get(f"{API_PREFIX}/shuttles")).status_code == 200
    assert (await client.get(f"{API_PREFIX}/shuttle-status")).status_code == 200
    assert (await client.get(f"{API_PREFIX}/announcements")).status_code == 200

    # 4. Public visitors CANNOT submit feedback or view private feedback (401)
    assert (
        await client.post(
            f"{API_PREFIX}/feedback",
            json={"category": "DELAY", "message": "unauthenticated attempt"},
        )
    ).status_code == 401
    assert (await client.get(f"{API_PREFIX}/feedback/mine")).status_code == 401
    assert (await client.get(f"{API_PREFIX}/auth/me")).status_code == 401

    # 5. Public visitors CANNOT perform admin operations (401)
    assert (await client.post(f"{API_PREFIX}/stops", json={"name": "hacked"})).status_code == 401
    assert (await client.post(f"{API_PREFIX}/routes", json={"code": "HACK", "name": "hacked"})).status_code == 401
    assert (await client.post(f"{API_PREFIX}/shuttles", json={"vehicle_code": "HACK"})).status_code == 401
    assert (
        await client.post(
            f"{API_PREFIX}/shuttle-status",
            json={"shuttle_id": verified_stop_id, "status": "ON_TIME"},
        )
    ).status_code == 401
