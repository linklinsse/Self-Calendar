from typing import Annotated
from fastapi import Depends
from sqlmodel import create_engine, Session, SQLModel

sqlite_file_name = "dev.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
db_engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(db_engine)
    print("Tables détectées:")
    for table_name in SQLModel.metadata.tables.keys():
        print(f"  - {table_name}")


def get_session():
    with Session(db_engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
