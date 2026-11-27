from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from app.api.dependencies import is_valid_csrf_pair
from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.middleware("http")
async def protect_cookie_authenticated_requests(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        current_settings = get_settings()
        origin = request.headers.get("origin")
        request_origin = f"{request.url.scheme}://{request.url.netloc}"
        same_origin = origin == request_origin
        origin_allowed = (
            not origin
            or same_origin
            or current_settings.allow_all_origins
            or origin in current_settings.cors_origin_list
        )
        if not origin_allowed:
            return JSONResponse(
                status_code=403,
                content={"detail": "Request origin is not allowed."},
            )

        # Skip CSRF check for initial authentication endpoints (login / registration).
        # An existing or stale access token cookie from a prior session must not block logging in.
        auth_exempt_paths = {
            f"{current_settings.api_v1_prefix}/auth/login",
            f"{current_settings.api_v1_prefix}/auth/admin/login",
            f"{current_settings.api_v1_prefix}/auth/register",
        }
        if request.url.path not in auth_exempt_paths:
            auth_header = request.headers.get("authorization", "")
            is_bearer_authenticated = auth_header.lower().startswith("bearer ")
            if (
                not is_bearer_authenticated
                and request.cookies.get(current_settings.auth_cookie_name)
                and not same_origin
            ):
                csrf_cookie = request.cookies.get(current_settings.csrf_cookie_name)
                csrf_header = request.headers.get("x-csrf-token")
                if not is_valid_csrf_pair(csrf_cookie, csrf_header):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "A valid CSRF token is required."},
                    )

    return await call_next(request)


if settings.allow_all_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*", "X-Access-Token", "x-access-token", "X-CSRF-Token", "x-csrf-token"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*", "X-Access-Token", "x-access-token", "X-CSRF-Token", "x-csrf-token"],
    )

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
