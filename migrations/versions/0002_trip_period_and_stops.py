"""Trip gets a period and stops; old trips become a trip with two stops.

Every old trip (origin, destination, km, date) becomes a trip with
start_date = end_date = the old date, the old km as distance_km, and two
free-standing stops (place name = old origin and old destination).

The downgrade restores the old shape. It cannot be lossless for trips with
other stops: origin and destination are taken from the first and the last stop.

Revision ID: 0002_trip_period_and_stops
Revises: 0001_baseline
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_trip_period_and_stops"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

# Lightweight table descriptions for the data conversion (independent of the models).
trips = sa.table(
    "trips",
    sa.column("id", sa.Integer),
    sa.column("origin", sa.String),
    sa.column("destination", sa.String),
    sa.column("km", sa.Integer),
    sa.column("date", sa.Date),
    sa.column("start_date", sa.Date),
    sa.column("end_date", sa.Date),
    sa.column("distance_km", sa.Integer),
)
stops = sa.table(
    "stops",
    sa.column("trip_id", sa.Integer),
    sa.column("position", sa.Integer),
    sa.column("date", sa.Date),
    sa.column("place_name", sa.String),
)


def upgrade() -> None:
    op.create_table(
        "stops",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "trip_id",
            sa.Integer(),
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("place_name", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
    )
    with op.batch_alter_table("trips") as batch:
        batch.add_column(sa.Column("start_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("end_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("distance_km", sa.Integer(), nullable=True))

    op.execute(
        trips.update().values(
            start_date=trips.c.date, end_date=trips.c.date, distance_km=trips.c.km
        )
    )
    for position, source in ((1, trips.c.origin), (2, trips.c.destination)):
        op.execute(
            stops.insert().from_select(
                ["trip_id", "position", "date", "place_name"],
                sa.select(trips.c.id, sa.literal(position), trips.c.date, source),
            )
        )

    with op.batch_alter_table("trips") as batch:
        batch.alter_column("start_date", existing_type=sa.Date(), nullable=False)
        batch.alter_column("end_date", existing_type=sa.Date(), nullable=False)
        batch.drop_column("origin")
        batch.drop_column("destination")
        batch.drop_column("km")
        batch.drop_column("date")


def downgrade() -> None:
    with op.batch_alter_table("trips") as batch:
        batch.add_column(sa.Column("origin", sa.String(), nullable=True))
        batch.add_column(sa.Column("destination", sa.String(), nullable=True))
        batch.add_column(sa.Column("km", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("date", sa.Date(), nullable=True))

    def place(order):
        return (
            sa.select(stops.c.place_name)
            .where(stops.c.trip_id == trips.c.id)
            .order_by(*order)
            .limit(1)
            .scalar_subquery()
        )

    op.execute(
        trips.update().values(
            date=trips.c.start_date,
            km=sa.func.coalesce(trips.c.distance_km, 0),
            origin=sa.func.coalesce(place([stops.c.date, stops.c.position]), ""),
            destination=sa.func.coalesce(
                place([stops.c.date.desc(), stops.c.position.desc()]), ""
            ),
        )
    )

    with op.batch_alter_table("trips") as batch:
        batch.alter_column("origin", existing_type=sa.String(), nullable=False)
        batch.alter_column("destination", existing_type=sa.String(), nullable=False)
        batch.alter_column("km", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("date", existing_type=sa.Date(), nullable=False)
        batch.drop_column("start_date")
        batch.drop_column("end_date")
        batch.drop_column("distance_km")
    op.drop_table("stops")
