from typing import List

from fastapi import HTTPException
from sqlmodel import select

from app.common.contexts.loged_user_context import get_loged_user_context
from app.common.db_connection import SessionDep
from app.common.decorators.db_session_injector import db_session_injector
from app.common.utils.verif_user_right_calendar import verif_user_right_calendar
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_event_model import ObjEventModel
from app.schemas.obj_event_schema import (
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)


@db_session_injector
def create_event(
    new_event: ObjEventSchemaCreate, db_session: SessionDep
) -> ObjEventSchemaComplete:
    """Create a new event inside an existing calendar.

    Requires at least "P" (Participer) permission on the target calendar.
    Returns 404 instead of 403 if the calendar is inaccessible, to avoid
    leaking its existence.
    """
    db_calendar = db_session.get(ObjCalendarModel, new_event.calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_calendar, "P"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Calendar not found")

    db_event = ObjEventModel.model_validate(new_event)

    db_session.add(db_event)
    db_session.commit()
    db_session.refresh(db_event)

    return db_event


@db_session_injector
def get_all_event_between(
    calendar_id: str,
    from_date: int,
    to_date: int,
    category_id: str | None,
    db_session: SessionDep,
) -> List[ObjEventSchemaComplete]:
    """Return all events in a calendar that overlap a given time range.

    The range check uses an overlap condition:
        event.date_end >= from_date  AND  event.date_start <= to_date
    This correctly includes events that start before or end after the range
    boundaries (partial overlaps are included).

    Args:
        calendar_id:  The calendar to query.
        from_date:    Range start as a Unix timestamp (inclusive).
        to_date:      Range end as a Unix timestamp (inclusive).
        category_id:  Optional filter — only return events of this category.

    Requires at least "C" (Consulter / read) permission.
    """
    db_calendar = db_session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_calendar, "C"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Calendar not found")

    statement = select(ObjEventModel).where(
        ObjEventModel.calendar_id == calendar_id,
        ObjEventModel.date_end >= from_date,
        ObjEventModel.date_start <= to_date,
    )

    # Optionally narrow results to a specific category
    if category_id is not None:
        statement = statement.where(ObjEventModel.category_id == category_id)

    results = db_session.exec(statement)
    return results.all()


@db_session_injector
def get_event(event_id: str, db_session: SessionDep) -> ObjEventSchemaComplete:
    """Fetch a single event by ID.

    Requires at least "C" (Consulter / read) permission on the parent calendar.
    Returns 404 if the event does not exist or the user has no access.
    """
    db_event = db_session.get(ObjEventModel, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "C"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Event not found")

    return db_event


@db_session_injector
def edit_event(
    event_id: str, edited_event: ObjEventSchemaEdit, db_session: SessionDep
) -> ObjEventSchemaComplete:
    """Update an event's fields (PATCH semantics — only provided fields are updated).

    Requires at least "P" (Participer) permission on the parent calendar.
    """
    db_event = db_session.get(ObjEventModel, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "P"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Event not found")

    # Apply only the fields that were explicitly provided in the request body
    update_data = edited_event.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    db_session.add(db_event)
    db_session.commit()
    db_session.refresh(db_event)

    return db_event


@db_session_injector
def delete_event(event_id: str, db_session: SessionDep):
    """Permanently delete an event.

    Requires at least "P" (Participer) permission on the parent calendar.
    """
    db_event = db_session.get(ObjEventModel, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "P"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Event not found")

    db_session.delete(db_event)
    db_session.commit()
