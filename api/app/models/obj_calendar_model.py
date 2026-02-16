from uuid import uuid4
from sqlmodel import Field, SQLModel


class ObjCalendarModel(SQLModel, table=True):
    __tablename__ = "obj_calendar"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    title: str = Field(nullable=False)
    description: str | None = Field(nullable=True, default="")
    color: str = Field(nullable=True, min_length=7, max_length=7)
