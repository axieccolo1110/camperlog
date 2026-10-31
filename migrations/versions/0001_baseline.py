"""Baseline: the schema before the realignment (trips, fuel_entries).

Production databases that were created by the former ``create_all`` already have
these tables. Mark them with ``alembic stamp 0001_baseline`` instead of
running this revision.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("km", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
    )
    op.create_table(
        "fuel_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("liters", sa.Float(), nullable=False),
        sa.Column("price_per_liter", sa.Float(), nullable=False),
        sa.Column("odometer", sa.Integer(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("fuel_entries")
    op.drop_table("trips")
