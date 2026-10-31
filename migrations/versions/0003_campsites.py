"""Campsites: places of their own, independent of trips.

Revision ID: 0003_campsites
Revises: 0002_trip_period_and_stops
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_campsites"
down_revision = "0002_trip_period_and_stops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campsites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="bookmarked"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "playground", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "pets_allowed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("external_url", sa.String(), nullable=True),
        sa.CheckConstraint(
            "status IN ('visited', 'bookmarked')", name="ck_campsites_status"
        ),
    )


def downgrade() -> None:
    op.drop_table("campsites")
