from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import FeedbackCategory, FeedbackStatus, UserRole
from app.models.feedback import Feedback
from app.models.route import Route
from app.models.shuttle import Shuttle
from app.models.stop import Stop
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackStatusUpdate


def _validate_related_record(
    db: Session,
    model: type[Route] | type[Stop] | type[Shuttle],
    record_id: UUID | None,
    name: str,
) -> None:
    if record_id is not None and db.get(model, record_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name} not found.",
        )


def create_feedback(
    db: Session,
    payload: FeedbackCreate,
    current_user: User,
) -> Feedback:
    _validate_related_record(db, Route, payload.route_id, "Route")
    _validate_related_record(db, Stop, payload.stop_id, "Stop")
    _validate_related_record(db, Shuttle, payload.shuttle_id, "Shuttle")

    feedback = Feedback(
        user_id=current_user.id,
        category=payload.category.value,
        message=payload.message,
        rating=payload.rating,
        status=FeedbackStatus.PENDING.value,
        route_id=payload.route_id,
        stop_id=payload.stop_id,
        shuttle_id=payload.shuttle_id,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def list_all_feedback(
    db: Session,
    *,
    feedback_status: FeedbackStatus | None,
    category: FeedbackCategory | None,
    skip: int,
    limit: int,
) -> tuple[list[Feedback], int]:
    filters = []
    if feedback_status is not None:
        filters.append(Feedback.status == feedback_status.value)
    if category is not None:
        filters.append(Feedback.category == category.value)
    total = db.scalar(select(func.count(Feedback.id)).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Feedback)
            .where(*filters)
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )
    return items, total


def list_user_feedback(
    db: Session,
    user_id: UUID,
    *,
    skip: int,
    limit: int,
) -> tuple[list[Feedback], int]:
    filters = [Feedback.user_id == user_id]
    total = db.scalar(select(func.count(Feedback.id)).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Feedback)
            .where(*filters)
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )
    return items, total


def get_feedback(
    db: Session,
    feedback_id: UUID,
    current_user: User,
) -> Feedback:
    feedback = db.get(Feedback, feedback_id)
    if feedback is None or (
        current_user.role != UserRole.ADMIN.value
        and feedback.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found.",
        )
    return feedback


def get_feedback_for_admin(db: Session, feedback_id: UUID) -> Feedback:
    feedback = db.scalar(
        select(Feedback).where(Feedback.id == feedback_id).with_for_update()
    )
    if feedback is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found.",
        )
    return feedback


def update_feedback_status(
    db: Session,
    feedback: Feedback,
    payload: FeedbackStatusUpdate,
    current_admin: User,
) -> Feedback:
    updates = payload.model_dump(exclude_unset=True)
    feedback.status = payload.status.value
    if "admin_response" in updates:
        feedback.admin_response = updates["admin_response"]
    feedback.reviewed_by_id = current_admin.id
    db.commit()
    db.refresh(feedback)
    return feedback
