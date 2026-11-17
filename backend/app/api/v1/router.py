from fastapi import APIRouter

from app.api.v1.announcements import router as announcements_router
from app.api.v1.auth import router as auth_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.routes import router as routes_router
from app.api.v1.shuttles import router as shuttles_router
from app.api.v1.shuttle_status import router as shuttle_status_router
from app.api.v1.stops import router as stops_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(announcements_router)
api_router.include_router(feedback_router)
api_router.include_router(stops_router)
api_router.include_router(routes_router)
api_router.include_router(shuttles_router)
api_router.include_router(shuttle_status_router)
