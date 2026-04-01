from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.obj_calendar_model import ObjCalendarModel


class LnkUserCalendarModel(SQLModel, table=True):
    """Join table linking users to calendars with an associated permission level.

    The `right` field holds a single character representing the user's
    permission on the calendar:
        "C" — Consulter  (read-only)
        "P" — Participer (can create/edit events)
        "O" — Owner      (full control)
    """

    __tablename__ = "lnk_user_calendar"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    user_id: str = Field(nullable=False, index=True, foreign_key="obj_user.id")
    calendar_id: str = Field(
        nullable=False, index=True, foreign_key="obj_calendar.id"
    )
    right: str = Field(nullable=False, min_length=1, max_length=1)

    obj_calendar: ObjCalendarModel = Relationship(back_populates="lnk_users")
