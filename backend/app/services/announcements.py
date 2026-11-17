from datetime import UTC, datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcements import AnnouncementCreate, AnnouncementUpdate


def _published_filter(now: datetime):
    return (
        Announcement.is_published.is_(True),
        or_(Announcement.starts_at.is_(None), Announcement.starts_at <= now),
        or_(Announcement.ends_at.is_(None), Announcement.ends_at > now),
    )


def list_announcements(
    db: Session,
    current_user: User,
    *,
    skip: int,
    limit: int,
) -> tuple[list[Announcement], int]:
    filters = []
    if current_user.role == UserRole.STUDENT.value:
        filters.extend(_published_filter(datetime.now(UTC)))

    total = db.scalar(select(func.count(Announcement.id)).where(*filters)) or 0
    publication_date = func.coalesce(Announcement.starts_at, Announcement.created_at)
    items = list(
        db.scalars(
            select(Announcement)
            .where(*filters)
            .order_by(publication_date.desc(), Announcement.created_at.desc(), Announcement.id)
            .offset(skip)
            .limit(limit)
        )
    )
    return items, total


def _get_announcement(db: Session, announcement_id: UUID) -> Announcement:
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found.",
        )
    return announcement


def get_announcement(
    db: Session,
    announcement_id: UUID,
    current_user: User,
) -> Announcement:
    announcement = _get_announcement(db, announcement_id)
    if current_user.role == UserRole.STUDENT.value:
        now = datetime.now(UTC)
        starts_at = announcement.starts_at
        ends_at = announcement.ends_at
        if starts_at is not None and starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=timezone.utc)
        if ends_at is not None and ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        if (
            not announcement.is_published
            or (starts_at is not None and starts_at > now)
            or (ends_at is not None and ends_at <= now)
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found.",
            )
    return announcement


def get_announcement_for_admin(
    db: Session,
    announcement_id: UUID,
) -> Announcement:
    announcement = db.scalar(
        select(Announcement)
        .where(Announcement.id == announcement_id)
        .with_for_update()
    )
    if announcement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found.",
        )
    return announcement


def create_announcement(
    db: Session,
    payload: AnnouncementCreate,
    current_admin: User,
) -> Announcement:
    announcement = Announcement(
        title=payload.title,
        body=payload.body,
        is_published=payload.is_published,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        published_by_id=current_admin.id,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def update_announcement(
    db: Session,
    announcement: Announcement,
    payload: AnnouncementUpdate,
) -> Announcement:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Provide at least one announcement field to update.",
        )

    starts_at = updates.get("starts_at", announcement.starts_at)
    ends_at = updates.get("ends_at", announcement.ends_at)
    if starts_at is not None and starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)
    if ends_at is not None and ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)
    if starts_at is not None and ends_at is not None and ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="ends_at must be later than starts_at.",
        )

    for field, value in updates.items():
        setattr(announcement, field, value)
    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, announcement: Announcement) -> None:
    db.delete(announcement)
    db.commit()
