"""Expand transport records for LPU, Phagwara, and Jalandhar.

Revision ID: 2f4d8c91a6b7
Revises: c5a72391f0d2
"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f4d8c91a6b7"
down_revision: Union[str, Sequence[str], None] = "c5a72391f0d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stops",
        sa.Column("service_area", sa.String(length=20), server_default="LPU", nullable=False),
    )
    op.add_column(
        "stops",
        sa.Column(
            "verification_status",
            sa.String(length=24),
            server_default="VERIFIED",
            nullable=False,
        ),
    )
    op.create_index("ix_stops_service_area", "stops", ["service_area"], unique=False)
    op.create_check_constraint(
        "ck_stops_service_area",
        "stops",
        "service_area IN ('LPU', 'PHAGWARA', 'JALANDHAR')",
    )
    op.create_check_constraint(
        "ck_stops_verification_status",
        "stops",
        "verification_status IN ('PLANNED', 'PENDING_VERIFICATION', 'VERIFIED')",
    )

    op.add_column(
        "routes",
        sa.Column("service_area", sa.String(length=20), server_default="LPU", nullable=False),
    )
    op.add_column(
        "routes",
        sa.Column(
            "verification_status",
            sa.String(length=24),
            server_default="VERIFIED",
            nullable=False,
        ),
    )
    op.create_index("ix_routes_service_area", "routes", ["service_area"], unique=False)
    op.create_check_constraint(
        "ck_routes_service_area",
        "routes",
        "service_area IN ('LPU', 'PHAGWARA', 'JALANDHAR')",
    )
    op.create_check_constraint(
        "ck_routes_verification_status",
        "routes",
        "verification_status IN ('PLANNED', 'PENDING_VERIFICATION', 'VERIFIED')",
    )

    op.add_column(
        "shuttles",
        sa.Column(
            "service_type",
            sa.String(length=32),
            server_default="CAMPUS_SHUTTLE",
            nullable=False,
        ),
    )
    op.add_column(
        "shuttles",
        sa.Column(
            "is_university_operated",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.add_column(
        "shuttles",
        sa.Column(
            "verification_status",
            sa.String(length=24),
            server_default="VERIFIED",
            nullable=False,
        ),
    )
    op.alter_column("shuttles", "capacity", nullable=True)
    op.create_index("ix_shuttles_service_type", "shuttles", ["service_type"], unique=False)
    op.create_check_constraint(
        "ck_shuttles_service_type",
        "shuttles",
        "service_type IN ('CAMPUS_SHUTTLE', 'E_RICKSHAW', 'AUTO_RICKSHAW', 'PUBLIC_BUS', 'TRAIN', 'OTHER')",
    )
    op.create_check_constraint(
        "ck_shuttles_verification_status",
        "shuttles",
        "verification_status IN ('PLANNED', 'PENDING_VERIFICATION', 'VERIFIED')",
    )

    op.drop_constraint("ck_shuttle_status_value", "shuttle_status", type_="check")
    op.create_check_constraint(
        "ck_shuttle_status_value",
        "shuttle_status",
        "status IN ('ON_TIME', 'DELAYED', 'UNAVAILABLE', 'CANCELLED', 'UNKNOWN', 'NOT_UPDATED')",
    )

    op.create_table(
        "route_service_types",
        sa.Column("route_id", sa.Uuid(), nullable=False),
        sa.Column("service_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "service_type IN ('CAMPUS_SHUTTLE', 'E_RICKSHAW', 'AUTO_RICKSHAW', 'PUBLIC_BUS', 'TRAIN', 'OTHER')",
            name="ck_route_service_types_value",
        ),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("route_id", "service_type"),
    )
    op.execute(
        "INSERT INTO route_service_types (route_id, service_type) "
        "SELECT id, 'CAMPUS_SHUTTLE' FROM routes"
    )

    candidate_stops = sa.table(
        "stops",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("service_area", sa.String()),
        sa.column("verification_status", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    candidates = [
        ("Main Gate", "Candidate location; pending verification.", "LPU"),
        ("Academic Area", "Candidate location; pending verification.", "LPU"),
        ("Hostel Area", "Candidate location; pending verification.", "LPU"),
        ("Shopping Area", "Candidate location; pending verification.", "LPU"),
        ("Phagwara Bus Stand", "Candidate location; pending verification.", "PHAGWARA"),
        ("Phagwara Railway Station", "Candidate location; pending verification.", "PHAGWARA"),
        ("Phagwara City Centre", "Candidate location; pending verification.", "PHAGWARA"),
        ("Jalandhar Bus Stand", "Candidate location; pending verification.", "JALANDHAR"),
        ("Jalandhar City Railway Station", "Candidate location; pending verification.", "JALANDHAR"),
        ("PAP Chowk", "Candidate location; pending verification.", "JALANDHAR"),
        ("Rama Mandi", "Candidate location; pending verification.", "JALANDHAR"),
    ]
    op.bulk_insert(
        candidate_stops,
        [
            {
                "id": uuid.uuid4(),
                "name": name,
                "description": description,
                "service_area": area,
                "verification_status": "PENDING_VERIFICATION",
                "is_active": False,
            }
            for name, description, area in candidates
        ],
    )


def downgrade() -> None:
    op.drop_table("route_service_types")
    op.drop_constraint("ck_shuttle_status_value", "shuttle_status", type_="check")
    op.create_check_constraint(
        "ck_shuttle_status_value",
        "shuttle_status",
        "status IN ('ON_TIME', 'DELAYED', 'UNAVAILABLE', 'NOT_UPDATED')",
    )
    op.drop_constraint("ck_shuttles_verification_status", "shuttles", type_="check")
    op.drop_constraint("ck_shuttles_service_type", "shuttles", type_="check")
    op.drop_index("ix_shuttles_service_type", table_name="shuttles")
    op.alter_column("shuttles", "capacity", nullable=False)
    op.drop_column("shuttles", "verification_status")
    op.drop_column("shuttles", "is_university_operated")
    op.drop_column("shuttles", "service_type")
    op.drop_constraint("ck_routes_verification_status", "routes", type_="check")
    op.drop_constraint("ck_routes_service_area", "routes", type_="check")
    op.drop_index("ix_routes_service_area", table_name="routes")
    op.drop_column("routes", "verification_status")
    op.drop_column("routes", "service_area")
    op.drop_constraint("ck_stops_verification_status", "stops", type_="check")
    op.drop_constraint("ck_stops_service_area", "stops", type_="check")
    op.drop_index("ix_stops_service_area", table_name="stops")
    op.drop_column("stops", "verification_status")
    op.drop_column("stops", "service_area")
