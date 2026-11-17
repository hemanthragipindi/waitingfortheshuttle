"""Add an optional feedback rating.

Revision ID: c5a72391f0d2
Revises: 7b94256398bc
Create Date: 2026-11-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5a72391f0d2"
down_revision: Union[str, Sequence[str], None] = "7b94256398bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("feedback", sa.Column("rating", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_feedback_rating_range",
        "feedback",
        "rating IS NULL OR rating BETWEEN 1 AND 5",
    )


def downgrade() -> None:
    op.drop_constraint("ck_feedback_rating_range", "feedback", type_="check")
    op.drop_column("feedback", "rating")
