from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from app.api.dependencies import is_valid_csrf_pair
from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def protect_cookie_authenticated_requests(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        request_origin = f"{request.url.scheme}://{request.url.netloc}"
        same_origin = origin == request_origin
        if origin and not same_origin and origin not in settings.cors_origin_list:
            return JSONResponse(
                status_code=403,
                content={"detail": "Request origin is not allowed."},
            )

        if request.cookies.get(settings.auth_cookie_name) and not same_origin:
            csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
            csrf_header = request.headers.get("x-csrf-token")
            if not is_valid_csrf_pair(csrf_cookie, csrf_header):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "A valid CSRF token is required."},
                )

    return await call_next(request)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
