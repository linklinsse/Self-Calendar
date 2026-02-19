from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.obj_calendar_model import ObjCalendarModel


class ObjEventModel(SQLModel, table=True):
    __tablename__ = "obj_event"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    calendar_id: str = Field(
        nullable=False, index=True, foreign_key="obj_calendar.id"
    )
    title: str = Field(nullable=False, max_length=255)
    description: str | None = Field(default=None)
    date_start: int = Field(nullable=False, index=True)
    date_end: int = Field(nullable=False, index=True)
    category_id: str | None = Field(default=None)  # TODO
    adresse: str | None = Field(nullable=True, max_length=255)
    reminder: str | None = Field(nullable=True, max_length=255)
    recurrence_id: str | None = Field(default=None)  # TODO

    obj_calendar: ObjCalendarModel = Relationship(back_populates="obj_events")
