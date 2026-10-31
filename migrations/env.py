"""Alembic environment. The database comes from camperlog.db, like in the app."""

from logging.config import fileConfig

from alembic import context

from camperlog.db import get_database_url, get_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with get_engine().connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        if is_sqlite:
            # Batch mode rebuilds tables (create new, copy, drop old, rename). With
            # foreign keys on, dropping the old table would cascade-delete rows of
            # tables that reference it. SQLite recommends turning them off while the
            # schema changes. (Must happen before any statement starts a transaction.)
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        try:
            # Batch mode: SQLite cannot alter columns in place.
            context.configure(connection=connection, render_as_batch=True)
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if is_sqlite:
                connection.commit()
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
