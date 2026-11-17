from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_student, get_current_user
from app.core.enums import FeedbackCategory, FeedbackStatus
from app.db.session import get_db_session
from app.models.feedback import Feedback
from app.models.user import User
from app.schemas.common import Page
from app.schemas.feedback import FeedbackCreate, FeedbackRead, FeedbackStatusUpdate
from app.services.feedback import (
    create_feedback,
    get_feedback,
    get_feedback_for_admin,
    list_all_feedback,
    list_user_feedback,
    update_feedback_status,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    payload: FeedbackCreate,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db_session),
) -> Feedback:
    return create_feedback(db, payload, current_student)


@router.get("", response_model=Page[FeedbackRead])
def read_all_feedback(
    feedback_status: FeedbackStatus | None = Query(default=None, alias="status"),
    category: FeedbackCategory | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Page[FeedbackRead]:
    items, total = list_all_feedback(
        db,
        feedback_status=feedback_status,
        category=category,
        skip=skip,
        limit=limit,
    )
    return Page[FeedbackRead](items=items, total=total, skip=skip, limit=limit)


@router.get("/mine", response_model=Page[FeedbackRead])
def read_my_feedback(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Page[FeedbackRead]:
    items, total = list_user_feedback(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
    )
    return Page[FeedbackRead](items=items, total=total, skip=skip, limit=limit)


@router.get("/{feedback_id}", response_model=FeedbackRead)
def read_feedback(
    feedback_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Feedback:
    return get_feedback(db, feedback_id, current_user)


@router.patch("/{feedback_id}/status", response_model=FeedbackRead)
def edit_feedback_status(
    feedback_id: UUID,
    payload: FeedbackStatusUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> Feedback:
    feedback = get_feedback_for_admin(db, feedback_id)
    return update_feedback_status(db, feedback, payload, current_admin)
