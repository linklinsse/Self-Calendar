from uuid import uuid4
from typing import ClassVar, List
from sqlmodel import Field, Relationship, SQLModel, Column, LargeBinary

class ObjEventRecurenceModel(SQLModel, table=True):
    """Database model for a calendar event recurence."""

    __tablename__ = "obj_event_recurence"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()), index=True)
    type: str = Field(nullable=False, min_length=1, max_length=1, default='D')
    interval: int = Field(nullable=False)
    days: str | None  = Field(nullable=True, min_length=7, max_length=7)
    endType: str = Field(nullable=False, min_length=1, max_length=1, default='N')
    count: int | None  = Field(nullable=True)
    until: int | None  = Field(nullable=True)

    obj_event: List["ObjEventModel"] = Relationship(
        back_populates="obj_recurence"
    )