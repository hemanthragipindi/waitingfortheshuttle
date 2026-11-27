import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user
from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.auth import LoginRequest, StudentRegistration
from app.schemas.users import UserRead
from app.services.auth_service import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    authenticate_user,
    register_student,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def set_auth_cookies(response: Response, user: User) -> str:
    settings = get_settings()
    if settings.app_env.lower() == "production" and not settings.auth_cookie_secure:
        raise RuntimeError("AUTH_COOKIE_SECURE must be true in production.")
    if settings.auth_cookie_samesite == "none" and not settings.auth_cookie_secure:
        raise RuntimeError("AUTH_COOKIE_SECURE must be true when SameSite=None.")

    response.headers["Cache-Control"] = "no-store"
    token = create_access_token(user.id)
    response.headers["X-Access-Token"] = token
    max_age = settings.jwt_access_token_minutes * 60
    cookie_options = {
        "max_age": max_age,
        "path": "/",
        "domain": settings.auth_cookie_domain,
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
    }
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        **cookie_options,
    )
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        **cookie_options,
    )
    response.headers["X-CSRF-Token"] = csrf_token
    return token


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    cookie_options = {
        "path": "/",
        "domain": settings.auth_cookie_domain,
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
    }
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        **cookie_options,
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        httponly=False,
        **cookie_options,
    )


def _authenticate(
    credentials: LoginRequest,
    expected_role: UserRole,
    response: Response,
    db: Session,
) -> User:
    try:
        user = authenticate_user(
            db,
            email=str(credentials.email),
            password=credentials.password,
            expected_role=expected_role,
        )
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token = set_auth_cookies(response, user)
    user.access_token = token
    return user


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    registration: StudentRegistration,
    response: Response,
    db: Session = Depends(get_db_session),
) -> User:
    try:
        user = register_student(db, registration)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc

    token = set_auth_cookies(response, user)
    user.access_token = token
    return user


@router.post("/login", response_model=UserRead)
def student_login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db_session),
) -> User:
    return _authenticate(credentials, UserRole.STUDENT, response, db)


@router.post("/admin/login", response_model=UserRead)
def admin_login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db_session),
) -> User:
    return _authenticate(credentials, UserRole.ADMIN, response, db)


@router.get("/me", response_model=UserRead)
def read_current_user(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
) -> User:
    response.headers["Cache-Control"] = "no-store"
    settings = get_settings()
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    if csrf_cookie:
        response.headers["X-CSRF-Token"] = csrf_cookie
    return current_user


@router.get("/admin/me", response_model=UserRead)
def read_current_admin(
    request: Request,
    response: Response,
    current_admin: User = Depends(get_current_admin),
) -> User:
    response.headers["Cache-Control"] = "no-store"
    settings = get_settings()
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    if csrf_cookie:
        response.headers["X-CSRF-Token"] = csrf_cookie
    return current_admin


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_auth_cookies(response)
