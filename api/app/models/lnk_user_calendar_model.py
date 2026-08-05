from uuid import uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.obj_calendar_model import ObjCalendarModel


class LnkUserCalendarModel(SQLModel, table=True):
    """Join table linking users to calendars with an associated permission level.

    The `right` field holds a single character representing the user's
    permission on the calendar:
        "R" — Read only
        "W" — Read/Write (can create/edit events)
        "O" — Owner      (full control)
    """

    __tablename__ = "lnk_user_calendar"

    # A user has at most one membership per calendar. This was previously
    # enforced only by an application-level existence check in
    # create_lnk_user_calendar, which is a check-then-act race: two
    # concurrent requests both see no row and both insert, leaving the user
    # with two different permission levels on the same calendar and
    # verify_user_right_calendar picking whichever comes back first.
    __table_args__ = (
        UniqueConstraint("user_id", "calendar_id", name="uq_user_calendar"),
    )

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    user_id: str = Field(nullable=False, index=True, foreign_key="obj_user.id")
    calendar_id: str = Field(
        nullable=False, index=True, foreign_key="obj_calendar.id"
    )
    right: str = Field(nullable=False, min_length=1, max_length=1)  # stored as CalendarRight value

    obj_calendar: ObjCalendarModel = Relationship(back_populates="lnk_users")
