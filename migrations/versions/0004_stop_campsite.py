"""A stop can reference a campsite (and then takes over its place).

Revision ID: 0004_stop_campsite
Revises: 0003_campsites
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_stop_campsite"
down_revision = "0003_campsites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("stops") as batch:
        batch.add_column(sa.Column("campsite_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_stops_campsite_id", "campsites", ["campsite_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("stops") as batch:
        batch.drop_constraint("fk_stops_campsite_id", type_="foreignkey")
        batch.drop_column("campsite_id")
