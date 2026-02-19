from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel
from typing import List


class ObjCalendarModel(SQLModel, table=True):
    __tablename__ = "obj_calendar"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    title: str = Field(nullable=False, max_length=255)
    description: str | None = Field(nullable=True, default="")
    color: str = Field(nullable=True, min_length=7, max_length=7)

    lnk_users: List["LnkUserCalendarModel"] = Relationship(back_populates="obj_calendar")
    obj_events: List["ObjEventModel"] = Relationship(back_populates="obj_calendar")
