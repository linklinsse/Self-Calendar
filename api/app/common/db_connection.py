"""
app/common/db_connection.py
----------------------------
SQLModel engine, session factory, and FastAPI dependency.

The database URL is read from the environment via `settings.DB_URL`
(see app/common/config.py and the .env file).  No hard-coded URL lives
here – to switch databases, update .env only.
"""


# ---------------------------------------------------------------------------
# Database configuration
# SQLite is used for development. For production, switch to PostgreSQL or
# another supported engine by changing the URL and connect_args below.
# ---------------------------------------------------------------------------

from collections.abc import Generator
from pathlib import Path
from typing import Annotated, TYPE_CHECKING

from fastapi import Depends
from sqlalchemy import event, inspect
from sqlmodel import Session, create_engine

if TYPE_CHECKING:
    from alembic.config import Config

from app.common.config import settings

_connect_args: dict[str, object] = {}

# SQLite requires check_same_thread=False to work with FastAPI's thread pool.
if settings.DB_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

db_engine = create_engine(settings.DB_URL, connect_args=_connect_args)


if settings.DB_URL.startswith("sqlite"):
    # SQLite defaults foreign key enforcement to OFF (per-connection, not
    # persisted) — every `foreign_key=` declaration in models/ would
    # otherwise be decorative. Also enable WAL, which improves concurrent
    # read performance under SQLite's single-writer model.
    @event.listens_for(db_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


# Revision of the schema as it stood before Alembic was introduced. An
# existing database created by the old create_all() path has exactly these
# tables and no alembic_version, so it is stamped with this and then upgraded
# forward — rather than being mistaken for an empty database.
_BASELINE_REVISION = "1ec329c28cf4"


def _alembic_config() -> "Config":
    from alembic.config import Config

    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(Path(__file__).resolve().parents[2] / "migrations"),
    )
    return config


def create_db_and_tables() -> None:
    """Bring the database up to the latest migration.

    Replaces SQLModel.metadata.create_all(), which created missing tables and
    silently ignored every existing one — so any change to a table that
    already existed simply never reached the database, and the app ran
    against a schema that no longer matched its models.

    Three cases:

    * Fresh database — no tables at all. Migrations run from scratch.
    * Pre-Alembic database — has tables but no alembic_version. Stamped at
      the baseline (which is exactly what create_all() used to produce) and
      then upgraded. This is the path an existing deployment takes, and it
      must not be mistaken for a fresh database: running the baseline
      migration against real tables would fail on the first CREATE TABLE.
    * Already managed — upgrade to head, a no-op when already current.
    """
    from alembic import command
    from alembic.runtime.migration import MigrationContext

    with db_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_revision = context.get_current_revision()
        inspector = inspect(db_engine)
        has_tables = bool(set(inspector.get_table_names()) - {"alembic_version"})

    config = _alembic_config()

    if current_revision is None and has_tables:
        print(
            "Existing database with no migration history — stamping baseline "
            f"({_BASELINE_REVISION}) and upgrading."
        )
        command.stamp(config, _BASELINE_REVISION)

    command.upgrade(config, "head")
    print("Database schema is up to date.")


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(db_engine) as session:
        yield session


# Annotated type alias used as a FastAPI dependency in route signatures:
SessionDep = Annotated[Session, Depends(get_session)]
