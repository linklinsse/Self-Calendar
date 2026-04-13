from typing import List
from sqlmodel import Session, select

from app.common.contexts.loged_user_context import get_loged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verif_user_right_calendar import verif_user_right_calendar
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_event_model import ObjEventModel
from app.schemas.obj_event_schema import (
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)


def create_event(
    new_event: ObjEventSchemaCreate, session: Session
) -> ObjEventSchemaComplete:
    """Create a new event inside an existing calendar.

    Requires at least "W" (Write) permission on the target calendar.
    Returns 404 instead of 403 if the calendar is inaccessible, to avoid
    leaking its existence.
    """
    db_calendar = session.get(ObjCalendarModel, new_event.calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    if not verif_user_right_calendar(get_loged_user_context(), db_calendar, "W"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    db_event = ObjEventModel.model_validate(new_event)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)

    return db_event


def get_all_event_between(
    calendar_id: str,
    from_date: int,
    to_date: int,
    category_id: str | None,
    session: Session,
) -> List[ObjEventSchemaComplete]:
    """Return all events in a calendar that overlap a given time range.

    The overlap condition is:
        event.date_end >= from_date  AND  event.date_start <= to_date
    This correctly includes partial overlaps (events that start before or
    end after the range boundaries).

    Args:
        calendar_id:  The calendar to query.
        from_date:    Range start as a Unix timestamp (inclusive).
        to_date:      Range end as a Unix timestamp (inclusive).
        category_id:  Optional filter — only return events of this category.
        session:      Active database session.

    Requires at least "R" (read) permission.
    """
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    if not verif_user_right_calendar(get_loged_user_context(), db_calendar, "R"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    statement = select(ObjEventModel).where(
        ObjEventModel.calendar_id == calendar_id,
        ObjEventModel.date_end >= from_date,
        ObjEventModel.date_start <= to_date,
    )

    if category_id is not None:
        statement = statement.where(ObjEventModel.category_id == category_id)

    return session.exec(statement).all()


def get_event(event_id: str, session: Session) -> ObjEventSchemaComplete:
    """Fetch a single event by ID.

    Requires at least "R" (read) permission on the parent calendar.
    Returns 404 if the event does not exist or the user has no access.
    """
    db_event = session.get(ObjEventModel, event_id)
    if not db_event:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if not verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "R"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    return db_event


def edit_event(
    event_id: str, edited_event: ObjEventSchemaEdit, session: Session
) -> ObjEventSchemaComplete:
    """Update an event's fields (PATCH semantics — only provided fields are updated).

    Requires at least "W" (Write) permission on the parent calendar.
    """
    db_event = session.get(ObjEventModel, event_id)
    if not db_event:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if not verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "W"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    update_data = edited_event.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    session.add(db_event)
    session.commit()
    session.refresh(db_event)

    return db_event


def delete_event(event_id: str, session: Session) -> None:
    """Permanently delete an event.

    Requires at least "W" (Write) permission on the parent calendar.
    """
    db_event = session.get(ObjEventModel, event_id)
    if not db_event:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if not verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "W"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    session.delete(db_event)
    session.commit()
