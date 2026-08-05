from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_event_recurence_model import ObjEventRecurenceModel


class ObjEventModel(SQLModel, table=True):
    """Database model for a calendar event."""

    __tablename__ = "obj_event"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    calendar_id: str = Field(
        nullable=False, index=True, foreign_key="obj_calendar.id"
    )
    title: str = Field(nullable=False, max_length=255)
    description: str | None = Field(default=None)
    date_start: int = Field(nullable=False, index=True)
    date_end: int = Field(nullable=False, index=True)
    # Real foreign key as of the 2026-08-02 migration. Before it, deleting a
    # category left events pointing at a row that no longer existed — the
    # event rendered uncategorised *and* became partially unmaintainable,
    # because any later PATCH echoing the stale id back was rejected by
    # _validate_category_in_calendar. delete_category clears these first;
    # this constraint is what stops a future write path reintroducing it.
    category_id: str | None = Field(
        default=None, nullable=True, foreign_key="obj_category.id"
    )
    # Per-event colour override. Null means "inherit from the category",
    # which is what almost every event does — hence nullable rather than
    # defaulted: a default would be indistinguishable from a user who
    # deliberately picked that exact colour, and there would be no way back
    # to inheriting once set.
    color: str | None = Field(default=None, nullable=True, max_length=7)
    address: str | None = Field(nullable=True, max_length=255)
    reminder: str | None = Field(nullable=True, max_length=255)
    # unique=True: the relationship is 1:1 in every code path, but nothing
    # said so, and a recurrence shared between two events meant deleting
    # either one destroyed the other's rule (delete_event cascades into the
    # attached recurrence). That was reachable remotely until recurence_id
    # was made server-owned; the constraint makes it unrepresentable.
    recurence_id: str | None = Field(
        default=None,
        nullable=True,
        unique=True,
        foreign_key="obj_event_recurence.id",
    )

    # Relationship back to the parent calendar
    obj_calendar: ObjCalendarModel = Relationship(back_populates="obj_events")
    obj_recurence: ObjEventRecurenceModel | None = Relationship(back_populates="obj_event")
