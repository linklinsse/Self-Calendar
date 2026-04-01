from typing import ClassVar, List
from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel


class ObjCalendarModel(SQLModel, table=True):
    """Database model for a calendar object."""

    __tablename__ = "obj_calendar"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    title: str = Field(nullable=False, max_length=255)
    description: str | None = Field(nullable=True, default="")
    # Hex color code (e.g. "#3A86FF") used for display purposes
    color: str = Field(nullable=True, min_length=7, max_length=7)

    # Relationships — not stored as columns, resolved by SQLModel via FK
    lnk_users: List["LnkUserCalendarModel"] = Relationship(
        back_populates="obj_calendar"
    )
    obj_events: List["ObjEventModel"] = Relationship(
        back_populates="obj_calendar"
    )

    # ClassVar: not a database column — computed at runtime from lnk_users
    # and injected into the response to expose the current user's permission
    # level (e.g. "R", "W", "O") without an extra query.
    # TODO: populate this field in the service layer before returning the model.
    user_right: ClassVar[str]
