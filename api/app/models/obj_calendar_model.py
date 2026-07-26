from typing import TYPE_CHECKING, List
from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # Only needed for static analysis — SQLModel resolves these forward
    # refs at runtime via its own registry, not via this module's imports.
    from app.models.lnk_user_calendar_model import LnkUserCalendarModel
    from app.models.obj_event_model import ObjEventModel


class ObjCalendarModel(SQLModel, table=True):
    """Database model for a calendar object."""

    __tablename__ = "obj_calendar"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    title: str = Field(nullable=False, max_length=255)
    description: str | None = Field(nullable=True, default="")
    color: str = Field(nullable=True, min_length=7, max_length=7)

    # Relationships — not stored as columns, resolved by SQLModel via FK
    lnk_users: List["LnkUserCalendarModel"] = Relationship(
        back_populates="obj_calendar"
    )
    obj_events: List["ObjEventModel"] = Relationship(
        back_populates="obj_calendar"
    )
