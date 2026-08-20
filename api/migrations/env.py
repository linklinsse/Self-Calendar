"""
Alembic environment.

Deliberately does NOT read a database URL from alembic.ini. The application
resolves DB_URL from conf/.env (see app/common/config.py), and a second
source of truth for "which database" is exactly how you end up migrating one
file while the app serves another. The URL and the engine come from the app.

Autogenerate compares app/models/ against the live database, so every model
module must be imported before `target_metadata` is read — importing a model
is what registers it on SQLModel.metadata. app.models imports them all.
"""

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

from app.common.config import settings
from app.common.db_connection import db_engine

# Registers every table on SQLModel.metadata. Without this, autogenerate
# sees an empty metadata and cheerfully generates a migration that drops
# every table in the database.
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (`alembic upgrade --sql`)."""
    context.configure(
        url=settings.DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite cannot ALTER most things in place; batch mode rebuilds the
        # table instead. Harmless on other backends, and required here for
        # anything touching a constraint.
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the app's own engine."""
    with db_engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
