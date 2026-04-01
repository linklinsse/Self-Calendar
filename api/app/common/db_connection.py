from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel

# ---------------------------------------------------------------------------
# Database configuration
# SQLite is used for development. For production, switch to PostgreSQL or
# another supported engine by changing the URL and connect_args below.
# ---------------------------------------------------------------------------
sqlite_file_name = "dev.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False is required for SQLite when used with FastAPI
# because FastAPI can handle multiple threads for a single request.
connect_args = {"check_same_thread": False}
db_engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    """Create all tables registered in SQLModel metadata if they don't exist."""
    SQLModel.metadata.create_all(db_engine)
    print("Tables detected:")
    for table_name in SQLModel.metadata.tables.keys():
        print(f"  - {table_name}")


def get_session():
    """Yield a SQLModel Session and close it automatically when done."""
    with Session(db_engine) as session:
        yield session


# Annotated type alias used as a FastAPI dependency in route signatures:
#   def my_route(db_session: SessionDep): ...
SessionDep = Annotated[Session, Depends(get_session)]
