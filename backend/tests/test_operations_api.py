from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.announcement import Announcement
from app.models.feedback import Feedback
from app.models.shuttle_status import ShuttleStatus
from app.models.user import User

API_PREFIX = "/api/v1"
ADMIN_EMAIL = "operations-admin-test@example.com"
ADMIN_PASSWORD = "test-only-operations-admin-password"
STUDENT_EMAIL = "operations-student-test@example.com"
STUDENT_PASSWORD = "test-only-operations-student-password"
OTHER_STUDENT_EMAIL = "other-operations-student-test@example.com"
OTHER_STUDENT_PASSWORD = "test-only-other-operations-student-password"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def operations_engine(monkeypatch: pytest.MonkeyPatch) -> Generator:
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
                    full_name="TEST ONLY Operations Admin",
                    password_hash=hash_password(ADMIN_PASSWORD),
                    role=UserRole.ADMIN.value,
                ),
                User(
                    email=STUDENT_EMAIL,
                    full_name="TEST ONLY Operations Student",
                    password_hash=hash_password(STUDENT_PASSWORD),
                    role=UserRole.STUDENT.value,
                ),
                User(
                    email=OTHER_STUDENT_EMAIL,
                    full_name="TEST ONLY Other Student",
                    password_hash=hash_password(OTHER_STUDENT_PASSWORD),
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
async def operations_client(operations_engine):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


def _csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    return {
        "Origin": "http://127.0.0.1:5173",
        "X-CSRF-Token": client.cookies.get("p05_csrf_token"),
    }


async def _login_admin(client: httpx.AsyncClient) -> dict[str, str]:
    client.cookies.clear()
    response = await client.post(
        f"{API_PREFIX}/auth/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return _csrf_headers(client)


async def _login_student(
    client: httpx.AsyncClient,
    *,
    email: str = STUDENT_EMAIL,
    password: str = STUDENT_PASSWORD,
) -> dict[str, str]:
    client.cookies.clear()
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return _csrf_headers(client)


@pytest.mark.anyio
async def test_shuttle_status_workflow_and_permissions(
    operations_client: httpx.AsyncClient,
    operations_engine,
) -> None:
    client = operations_client
    assert (await client.get(f"{API_PREFIX}/shuttle-status")).status_code == 200
    admin_headers = await _login_admin(client)

    stop = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY Status Stop"},
        headers=admin_headers,
    )
    assert stop.status_code == 201
    route = await client.post(
        f"{API_PREFIX}/routes",
        json={
            "code": "TEST-STATUS-ROUTE",
            "name": "TEST ONLY Status Route",
            "stop_ids": [stop.json()["id"]],
        },
        headers=admin_headers,
    )
    assert route.status_code == 201
    shuttle = await client.post(
        f"{API_PREFIX}/shuttles",
        json={
            "vehicle_code": "TEST-STATUS-SHUTTLE",
            "capacity": 20,
            "route_id": route.json()["id"],
        },
        headers=admin_headers,
    )
    assert shuttle.status_code == 201
    shuttle_id = shuttle.json()["id"]

    initial = await client.get(
        f"{API_PREFIX}/shuttle-status/shuttle/{shuttle_id}"
    )
    assert initial.status_code == 200
    assert initial.json()["status"] == "NOT_UPDATED"
    assert initial.json()["last_updated_at"] is None
    assert initial.json()["shuttle"]["is_active"] is True

    missing_shuttle = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={
            "shuttle_id": "00000000-0000-0000-0000-000000000001",
            "status": "DELAYED",
        },
        headers=admin_headers,
    )
    assert missing_shuttle.status_code == 404
    invalid_status = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={"shuttle_id": shuttle_id, "status": "ARRIVING"},
        headers=admin_headers,
    )
    assert invalid_status.status_code == 422
    missing_fields = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={"status": "DELAYED"},
        headers=admin_headers,
    )
    assert missing_fields.status_code == 422

    created = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={
            "shuttle_id": shuttle_id,
            "status": "DELAYED",
            "message": "TEST ONLY manual delay update",
        },
        headers=admin_headers,
    )
    assert created.status_code == 201
    assert created.json()["status"] == "DELAYED"
    assert created.json()["shuttle"]["vehicle_code"] == "TEST-STATUS-SHUTTLE"
    assert created.json()["created_at"]
    later_update = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={
            "shuttle_id": shuttle_id,
            "status": "ON_TIME",
            "message": "TEST ONLY later manual update",
        },
        headers=admin_headers,
    )
    assert later_update.status_code == 201
    later_recorded_at = datetime.fromisoformat(later_update.json()["created_at"])
    first_recorded_at = datetime.fromisoformat(created.json()["created_at"])
    assert later_recorded_at > first_recorded_at

    current_list = await client.get(f"{API_PREFIX}/shuttle-status")
    assert current_list.status_code == 200
    assert current_list.json()["total"] == 1
    assert current_list.json()["items"][0]["status"] == "ON_TIME"

    route_status = await client.get(
        f"{API_PREFIX}/shuttle-status/route/{route.json()['id']}"
    )
    assert route_status.status_code == 200
    assert route_status.json()["items"][0]["status"] == "ON_TIME"
    assert route_status.json()["items"][0]["shuttle"]["id"] == shuttle_id

    history = await client.get(
        f"{API_PREFIX}/shuttle-status/shuttle/{shuttle_id}/history"
    )
    assert history.status_code == 200
    assert history.json()["total"] == 2
    assert history.json()["items"][0]["message"] == "TEST ONLY later manual update"
    assert history.json()["items"][1]["message"] == "TEST ONLY manual delay update"

    student_headers = await _login_student(client)
    denied = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={"shuttle_id": shuttle_id, "status": "ON_TIME"},
        headers=student_headers,
    )
    assert denied.status_code == 403
    assert (await client.get(f"{API_PREFIX}/shuttle-status")).status_code == 200

    with Session(operations_engine) as session:
        assert session.scalar(
            select(ShuttleStatus.id).where(
                ShuttleStatus.id == UUID(created.json()["id"])
            )
        ) is not None


@pytest.mark.anyio
async def test_announcement_and_feedback_workflows_and_access(
    operations_client: httpx.AsyncClient,
    operations_engine,
) -> None:
    client = operations_client
    assert (await client.get(f"{API_PREFIX}/announcements")).status_code == 200
    assert (await client.get(f"{API_PREFIX}/feedback")).status_code == 401
    admin_headers = await _login_admin(client)

    stop = await client.post(
        f"{API_PREFIX}/stops",
        json={"name": "TEST ONLY Feedback Stop"},
        headers=admin_headers,
    )
    route = await client.post(
        f"{API_PREFIX}/routes",
        json={
            "code": "TEST-FEEDBACK-ROUTE",
            "name": "TEST ONLY Feedback Route",
            "stop_ids": [stop.json()["id"]],
        },
        headers=admin_headers,
    )
    shuttle = await client.post(
        f"{API_PREFIX}/shuttles",
        json={
            "vehicle_code": "TEST-FEEDBACK-SHUTTLE",
            "capacity": 18,
            "route_id": route.json()["id"],
        },
        headers=admin_headers,
    )
    assert [stop.status_code, route.status_code, shuttle.status_code] == [201, 201, 201]

    now = datetime.now(timezone.utc)
    earlier = await client.post(
        f"{API_PREFIX}/announcements",
        json={
            "title": "TEST ONLY Earlier Notice",
            "body": "TEST ONLY Earlier description",
            "is_published": True,
            "starts_at": (now - timedelta(days=2)).isoformat(),
            "ends_at": (now + timedelta(days=2)).isoformat(),
        },
        headers=admin_headers,
    )
    later = await client.post(
        f"{API_PREFIX}/announcements",
        json={
            "title": "TEST ONLY Latest Notice",
            "body": "TEST ONLY Latest description",
            "is_published": True,
            "starts_at": (now - timedelta(days=1)).isoformat(),
        },
        headers=admin_headers,
    )
    draft = await client.post(
        f"{API_PREFIX}/announcements",
        json={
            "title": "TEST ONLY Draft",
            "body": "TEST ONLY not published",
        },
        headers=admin_headers,
    )
    assert [earlier.status_code, later.status_code, draft.status_code] == [201, 201, 201]
    assert earlier.json()["published_by_id"]

    invalid_dates = await client.post(
        f"{API_PREFIX}/announcements",
        json={
            "title": "TEST ONLY Invalid Dates",
            "body": "TEST ONLY invalid date range",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": now.isoformat(),
        },
        headers=admin_headers,
    )
    missing_body = await client.post(
        f"{API_PREFIX}/announcements",
        json={"title": "TEST ONLY Missing Body"},
        headers=admin_headers,
    )
    blank_announcement = await client.post(
        f"{API_PREFIX}/announcements",
        json={"title": "   ", "body": "TEST ONLY blank title"},
        headers=admin_headers,
    )
    assert invalid_dates.status_code == 422
    assert missing_body.status_code == 422
    assert blank_announcement.status_code == 422

    admin_announcements = await client.get(f"{API_PREFIX}/announcements")
    assert admin_announcements.status_code == 200
    assert admin_announcements.json()["total"] == 3

    student_headers = await _login_student(client)
    published_announcements = await client.get(f"{API_PREFIX}/announcements")
    assert published_announcements.status_code == 200
    assert published_announcements.json()["total"] == 2
    assert published_announcements.json()["items"][0]["id"] == later.json()["id"]
    hidden_draft = await client.get(
        f"{API_PREFIX}/announcements/{draft.json()['id']}"
    )
    assert hidden_draft.status_code == 404
    denied_announcement = await client.post(
        f"{API_PREFIX}/announcements",
        json={"title": "TEST ONLY unauthorized", "body": "TEST ONLY"},
        headers=student_headers,
    )
    assert denied_announcement.status_code == 403

    edited = await client.patch(
        f"{API_PREFIX}/announcements/{draft.json()['id']}",
        json={"is_published": True, "body": "TEST ONLY published draft"},
        headers=await _login_admin(client),
    )
    assert edited.status_code == 200
    invalid_update = await client.patch(
        f"{API_PREFIX}/announcements/{later.json()['id']}",
        json={"ends_at": (now - timedelta(days=3)).isoformat()},
        headers=await _login_admin(client),
    )
    empty_update = await client.patch(
        f"{API_PREFIX}/announcements/{draft.json()['id']}",
        json={},
        headers=await _login_admin(client),
    )
    assert invalid_update.status_code == 422
    assert empty_update.status_code == 422

    student_headers = await _login_student(client)
    submitted = await client.post(
        f"{API_PREFIX}/feedback",
        json={
            "category": "DELAY",
            "message": "TEST ONLY shuttle delay report",
            "rating": 4,
            "route_id": route.json()["id"],
            "stop_id": stop.json()["id"],
            "shuttle_id": shuttle.json()["id"],
        },
        headers=student_headers,
    )
    assert submitted.status_code == 201
    feedback_id = submitted.json()["id"]
    assert submitted.json()["status"] == "PENDING"
    assert submitted.json()["rating"] == 4
    assert submitted.json()["user_id"]
    assert (await client.get(f"{API_PREFIX}/feedback")).status_code == 403

    missing_reference = await client.post(
        f"{API_PREFIX}/feedback",
        json={
            "category": "SUGGESTION",
            "message": "TEST ONLY report with invalid stop",
            "stop_id": "00000000-0000-0000-0000-000000000001",
        },
        headers=student_headers,
    )
    missing_message = await client.post(
        f"{API_PREFIX}/feedback",
        json={"category": "DELAY"},
        headers=student_headers,
    )
    invalid_category = await client.post(
        f"{API_PREFIX}/feedback",
        json={"category": "INVALID", "message": "TEST ONLY invalid category"},
        headers=student_headers,
    )
    invalid_rating = await client.post(
        f"{API_PREFIX}/feedback",
        json={
            "category": "DELAY",
            "message": "TEST ONLY invalid rating",
            "rating": 6,
        },
        headers=student_headers,
    )
    blank_message = await client.post(
        f"{API_PREFIX}/feedback",
        json={"category": "SUGGESTION", "message": "   "},
        headers=student_headers,
    )
    assert missing_reference.status_code == 404
    assert missing_message.status_code == 422
    assert invalid_category.status_code == 422
    assert invalid_rating.status_code == 422
    assert blank_message.status_code == 422

    mine = await client.get(f"{API_PREFIX}/feedback/mine")
    assert mine.status_code == 200
    assert mine.json()["total"] == 1
    assert mine.json()["items"][0]["id"] == feedback_id

    other_student_headers = await _login_student(
        client,
        email=OTHER_STUDENT_EMAIL,
        password=OTHER_STUDENT_PASSWORD,
    )
    assert (
        await client.get(f"{API_PREFIX}/feedback/{feedback_id}")
    ).status_code == 404
    assert (
        await client.patch(
            f"{API_PREFIX}/feedback/{feedback_id}/status",
            json={"status": "RESOLVED"},
            headers=other_student_headers,
        )
    ).status_code == 403

    admin_headers = await _login_admin(client)
    feedback_list = await client.get(
        f"{API_PREFIX}/feedback",
        params={"status": "PENDING", "category": "DELAY"},
    )
    assert feedback_list.status_code == 200
    assert feedback_list.json()["total"] == 1
    assert feedback_list.json()["items"][0]["id"] == feedback_id

    review = await client.patch(
        f"{API_PREFIX}/feedback/{feedback_id}/status",
        json={"status": "RESOLVED", "admin_response": "TEST ONLY reviewed"},
        headers=admin_headers,
    )
    assert review.status_code == 200
    assert review.json()["status"] == "RESOLVED"
    assert review.json()["admin_response"] == "TEST ONLY reviewed"
    assert review.json()["reviewed_by_id"]
    status_only_review = await client.patch(
        f"{API_PREFIX}/feedback/{feedback_id}/status",
        json={"status": "RESOLVED"},
        headers=admin_headers,
    )
    assert status_only_review.status_code == 200
    assert status_only_review.json()["admin_response"] == "TEST ONLY reviewed"

    other_student_headers = await _login_student(
        client,
        email=OTHER_STUDENT_EMAIL,
        password=OTHER_STUDENT_PASSWORD,
    )
    other_feedback = await client.get(f"{API_PREFIX}/feedback/{feedback_id}")
    assert other_feedback.status_code == 404
    assert (
        await client.patch(
            f"{API_PREFIX}/feedback/{feedback_id}/status",
            json={"status": "DISMISSED"},
            headers=other_student_headers,
        )
    ).status_code == 403

    admin_headers = await _login_admin(client)
    deleted = await client.delete(
        f"{API_PREFIX}/announcements/{earlier.json()['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 204
    assert (
        await client.get(f"{API_PREFIX}/announcements/{earlier.json()['id']}")
    ).status_code == 404
    assert (
        await client.delete(
            f"{API_PREFIX}/announcements/00000000-0000-0000-0000-000000000001",
            headers=admin_headers,
        )
    ).status_code == 404

    with Session(operations_engine) as session:
        assert session.scalar(
            select(Feedback.id).where(Feedback.id == UUID(feedback_id))
        ) is not None
        assert session.scalar(
            select(Feedback.status).where(Feedback.id == UUID(feedback_id))
        ) == "RESOLVED"
        assert session.scalar(
            select(Announcement.id).where(
                Announcement.id == UUID(earlier.json()["id"])
            )
        ) is None
        assert session.scalar(select(ShuttleStatus.id)) is None


@pytest.mark.anyio
async def test_multi_area_services_verification_and_filters(
    operations_client: httpx.AsyncClient,
) -> None:
    client = operations_client
    admin_headers = await _login_admin(client)

    stop = await client.post(
        f"{API_PREFIX}/stops",
        json={
            "name": "TEST ONLY Phagwara Station",
            "service_area": "PHAGWARA",
            "verification_status": "PENDING_VERIFICATION",
        },
        headers=admin_headers,
    )
    assert stop.status_code == 201
    assert stop.json()["is_active"] is False
    stop_id = stop.json()["id"]

    verified_stop = await client.patch(
        f"{API_PREFIX}/stops/{stop_id}",
        json={"verification_status": "VERIFIED", "is_active": True},
        headers=admin_headers,
    )
    assert verified_stop.status_code == 200
    assert verified_stop.json()["is_active"] is True

    route = await client.post(
        f"{API_PREFIX}/routes",
        json={
            "code": "TEST-PHAGWARA-MULTI",
            "name": "TEST ONLY Phagwara interchange",
            "service_area": "PHAGWARA",
            "service_types": ["CAMPUS_SHUTTLE", "PUBLIC_BUS"],
            "stop_ids": [stop_id],
        },
        headers=admin_headers,
    )
    assert route.status_code == 201
    assert route.json()["service_types"] == ["CAMPUS_SHUTTLE", "PUBLIC_BUS"]
    route_id = route.json()["id"]

    campus_service = await client.post(
        f"{API_PREFIX}/shuttles",
        json={
            "vehicle_code": "TEST-PHAGWARA-CAMPUS",
            "capacity": 24,
            "route_id": route_id,
            "service_type": "CAMPUS_SHUTTLE",
        },
        headers=admin_headers,
    )
    public_service = await client.post(
        f"{API_PREFIX}/shuttles",
        json={
            "vehicle_code": "TEST-PHAGWARA-BUS",
            "capacity": None,
            "route_id": route_id,
            "service_type": "PUBLIC_BUS",
            "is_university_operated": False,
        },
        headers=admin_headers,
    )
    assert [campus_service.status_code, public_service.status_code] == [201, 201]
    assert public_service.json()["is_university_operated"] is False
    public_id = public_service.json()["id"]

    status_update = await client.post(
        f"{API_PREFIX}/shuttle-status",
        json={"shuttle_id": public_id, "status": "CANCELLED"},
        headers=admin_headers,
    )
    assert status_update.status_code == 201

    filtered_status = await client.get(
        f"{API_PREFIX}/shuttle-status",
        params={
            "service_area": "PHAGWARA",
            "service_type": "PUBLIC_BUS",
            "status": "CANCELLED",
        },
    )
    assert filtered_status.status_code == 200
    assert filtered_status.json()["total"] == 1

    student_headers = await _login_student(client)
    filtered_routes = await client.get(
        f"{API_PREFIX}/routes",
        params={
            "service_area": "PHAGWARA",
            "service_type": "PUBLIC_BUS",
            "destination": "Station",
            "status": "CANCELLED",
        },
        headers=student_headers,
    )
    assert filtered_routes.status_code == 200
    assert filtered_routes.json()["total"] == 1
