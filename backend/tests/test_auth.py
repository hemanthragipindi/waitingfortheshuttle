from collections.abc import Generator
from datetime import timedelta
from uuid import UUID

import httpx
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password, password_hash
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.user import User

API_PREFIX = "/api/v1/auth"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def auth_engine(monkeypatch: pytest.MonkeyPatch) -> Generator:
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
    yield engine
    app.dependency_overrides.clear()
    engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
async def client(auth_engine):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


async def register_student(client: httpx.AsyncClient, email: str = "student@example.com"):
    return await client.post(
        f"{API_PREFIX}/register",
        json={
            "email": email,
            "full_name": "TEST ONLY Student",
            "password": "test-only-long-password",
        },
    )


@pytest.mark.anyio
async def test_student_registration_login_profile_and_self_role_protection(
    client: httpx.AsyncClient,
    auth_engine,
) -> None:
    rejected_role = await client.post(
        f"{API_PREFIX}/register",
        json={
            "email": "role-test@example.com",
            "full_name": "TEST ONLY Student",
            "password": "test-only-long-password",
            "role": "ADMIN",
        },
    )
    assert rejected_role.status_code == 422

    registration = await register_student(client)
    assert registration.status_code == 201
    assert registration.json()["role"] == UserRole.STUDENT.value
    assert "password_hash" not in registration.json()
    assert "httponly" in registration.headers["set-cookie"].lower()

    with Session(auth_engine) as session:
        user = session.scalar(select(User).where(User.email == "student@example.com"))
        assert user is not None
        assert user.password_hash != "test-only-long-password"
        assert password_hash.verify("test-only-long-password", user.password_hash)

    me = await client.get(f"{API_PREFIX}/me")
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"
    assert (await client.get(f"{API_PREFIX}/admin/me")).status_code == 403

    logout = await client.post(
        f"{API_PREFIX}/logout",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "X-CSRF-Token": client.cookies.get("p05_csrf_token"),
        },
    )
    assert logout.status_code == 204
    assert (await client.get(f"{API_PREFIX}/me")).status_code == 401


@pytest.mark.anyio
async def test_login_rejects_bad_credentials_and_students_cannot_admin_login(
    client: httpx.AsyncClient,
) -> None:
    await register_student(client)
    client.cookies.clear()

    invalid_password = await client.post(
        f"{API_PREFIX}/login",
        json={"email": "student@example.com", "password": "incorrect-password"},
    )
    assert invalid_password.status_code == 401

    student_on_admin_login = await client.post(
        f"{API_PREFIX}/admin/login",
        json={"email": "student@example.com", "password": "test-only-long-password"},
    )
    assert student_on_admin_login.status_code == 401


@pytest.mark.anyio
async def test_admin_login_and_role_protected_endpoint(
    client: httpx.AsyncClient,
    auth_engine,
) -> None:
    with Session(auth_engine) as session:
        session.add(
            User(
                email="admin@example.com",
                full_name="TEST ONLY Admin",
                password_hash=hash_password("test-only-admin-password"),
                role=UserRole.ADMIN.value,
            )
        )
        session.commit()

    response = await client.post(
        f"{API_PREFIX}/admin/login",
        json={
            "email": "admin@example.com",
            "password": "test-only-admin-password",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.ADMIN.value
    assert (await client.get(f"{API_PREFIX}/admin/me")).status_code == 200


@pytest.mark.anyio
async def test_inactive_accounts_cannot_login_or_use_existing_tokens(
    client: httpx.AsyncClient,
    auth_engine,
) -> None:
    with Session(auth_engine) as session:
        user = User(
            email="inactive-test@example.com",
            full_name="TEST ONLY Inactive Student",
            password_hash=hash_password("test-only-inactive-password"),
            role=UserRole.STUDENT.value,
            is_active=False,
        )
        session.add(user)
        session.commit()
        user_id = user.id

    client.cookies.set("p05_access_token", create_access_token(user_id))
    assert (await client.get(f"{API_PREFIX}/me")).status_code == 401
    client.cookies.clear()
    login = await client.post(
        f"{API_PREFIX}/login",
        json={
            "email": "inactive-test@example.com",
            "password": "test-only-inactive-password",
        },
    )
    assert login.status_code == 401


@pytest.mark.anyio
async def test_expired_access_token_is_rejected(client: httpx.AsyncClient) -> None:
    registration = await register_student(client)
    user_id = registration.json()["id"]
    client.cookies.set(
        "p05_access_token",
        create_access_token(
            UUID(user_id),
            expires_delta=timedelta(seconds=-1),
        ),
    )

    response = await client.get(f"{API_PREFIX}/me")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_csrf_and_origin_checks_protect_cookie_mutations(
    client: httpx.AsyncClient,
) -> None:
    await register_student(client)

    missing_token = await client.post(
        f"{API_PREFIX}/logout",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert missing_token.status_code == 403

    foreign_origin = await client.post(
        f"{API_PREFIX}/logout",
        headers={
            "Origin": "https://attacker.example",
            "X-CSRF-Token": client.cookies.get("p05_csrf_token"),
        },
    )
    assert foreign_origin.status_code == 403

    same_origin_logout = await client.post(
        f"{API_PREFIX}/logout",
        headers={"Origin": "http://test"},
    )
    assert same_origin_logout.status_code == 204
