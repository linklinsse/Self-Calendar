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
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.common.config import settings

_connect_args: dict[str, object] = {}

# SQLite requires check_same_thread=False to work with FastAPI's thread pool.
if settings.DB_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

db_engine = create_engine(settings.DB_URL, connect_args=_connect_args)


def create_db_and_tables() -> None:
    """Create all SQLModel tables that have not been created yet."""
    SQLModel.metadata.create_all(db_engine)
    print("Tables detected:")
    for table_name in SQLModel.metadata.tables.keys():
        print(f"  - {table_name}")


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    with Session(db_engine) as session:
        yield session


# Annotated type alias used as a FastAPI dependency in route signatures:
SessionDep = Annotated[Session, Depends(get_session)]
