from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_optional_current_user
from app.db.session import get_db_session
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcements import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
)
from app.schemas.common import Page
from app.services.announcements import (
    create_announcement,
    delete_announcement,
    get_announcement,
    get_announcement_for_admin,
    list_announcements,
    update_announcement,
)

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=Page[AnnouncementRead])
def read_announcements(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
) -> Page[AnnouncementRead]:
    items, total = list_announcements(
        db,
        current_user,
        skip=skip,
        limit=limit,
    )
    return Page[AnnouncementRead](items=items, total=total, skip=skip, limit=limit)


@router.get("/{announcement_id}", response_model=AnnouncementRead)
def read_announcement(
    announcement_id: UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db_session),
) -> Announcement:
    return get_announcement(db, announcement_id, current_user)


@router.post(
    "",
    response_model=AnnouncementRead,
    status_code=status.HTTP_201_CREATED,
)
def add_announcement(
    payload: AnnouncementCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Announcement:
    return create_announcement(db, payload, current_admin)


@router.patch("/{announcement_id}", response_model=AnnouncementRead)
def edit_announcement(
    announcement_id: UUID,
    payload: AnnouncementUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Announcement:
    announcement = get_announcement_for_admin(db, announcement_id)
    return update_announcement(db, announcement, payload)


@router.delete(
    "/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_announcement(
    announcement_id: UUID,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Response:
    announcement = get_announcement_for_admin(db, announcement_id)
    delete_announcement(db, announcement)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
