from typing import List
from sqlmodel import Session, select, and_, or_

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verify_user_right_calendar import verify_user_right_calendar
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_event_model import ObjEventModel
from app.models.obj_event_recurence_model import ObjEventRecurenceModel
from app.schemas.obj_event_schema import (
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)
from app.services import obj_event_recurente_service



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

    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "W"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    if new_event.obj_recurence is not None:
        db_event_recurence = obj_event_recurente_service.create_event_recurence(
            new_event.obj_recurence,
            new_event.date_start,
            session
        )
        new_event.recurence_id = db_event_recurence.id
        new_event.obj_recurence = db_event_recurence

    db_event = ObjEventModel.model_validate(new_event)

    session.add(db_event)
    session.commit()
    session.refresh(db_event)

    return db_event


def get_all_event_between(
    calendar_ids: List[str],
    from_date: int | None,
    to_date: int | None,
    category_ids: str | None,
    session: Session,
) -> List[ObjEventSchemaComplete]:
    """Return all events in a calendar that overlap a given time range.

    The overlap condition is:
        event.date_end >= from_date  AND  event.date_start <= to_date
    This correctly includes partial overlaps (events that start before or
    end after the range boundaries).

    Args:
        calendar_ids:  The calendar to query.
        from_date:    Range start as a Unix timestamp (inclusive).
        to_date:      Range end as a Unix timestamp (inclusive).
        category_ids:  Optional filter — only return events of this category.
        session:      Active database session.

    Requires at least "R" (read) permission.
    """

    db_calendars = session.exec(select(ObjCalendarModel).where(ObjCalendarModel.id.in_(calendar_ids))).all()
    if len(db_calendars) == 0:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    for db_calendar in db_calendars:
        if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "R"):
            raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)


    statement = select(ObjEventModel).where(
        ObjEventModel.calendar_id.in_(calendar_ids),
        or_(
            # Non-recurring: must overlap the requested window
            and_(
                ObjEventModel.recurence_id.is_(None),
                ObjEventModel.date_end >= from_date,
                ObjEventModel.date_start <= to_date,
            ),
            # Recurring: fetch all that started before the window ends;
            # recurrence expansion + filtering happens in the app layer
            and_(
                ObjEventModel.recurence_id.is_not(None),
                ObjEventModel.date_start <= to_date,
                or_(
                    ObjEventRecurenceModel.estimated_end_date.is_(None),  # endType == 'N' (never)
                    ObjEventRecurenceModel.estimated_end_date >= from_date,
                ),
            ),
        ),
    ).join(
        ObjEventRecurenceModel,
        ObjEventModel.recurence_id == ObjEventRecurenceModel.id,
        isouter=True,  # keep non-recurring events (recurence_id == None)
    )

    if category_ids is not None:
        statement = statement.where(ObjEventModel.category_id.in_(category_ids))

    return session.exec(statement).all()


def get_event(event_id: str, session: Session) -> ObjEventSchemaComplete:
    """Fetch a single event by ID.

    Requires at least "R" (read) permission on the parent calendar.
    Returns 404 if the event does not exist or the user has no access.
    """
    db_event = session.get(ObjEventModel, event_id)
    if not db_event:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if not verify_user_right_calendar(
        get_logged_user_context(), db_event.obj_calendar, "R"
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

    if not verify_user_right_calendar(
        get_logged_user_context(), db_event.obj_calendar, "W"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    # Only touch the existing recurrence when the request actually replaces
    # it — deleting it unconditionally here would strip recurrence off an
    # event whenever an unrelated field (e.g. the title) is edited.
    if edited_event.obj_recurence is not None:
        # date_start is optional on a PATCH — fall back to the event's
        # existing start so compute_estimated_end() always gets an int.
        recurence_date_start = (
            edited_event.date_start
            if edited_event.date_start is not None
            else db_event.date_start
        )
        db_event_recurence = obj_event_recurente_service.create_event_recurence(
            edited_event.obj_recurence,
            recurence_date_start,
            session
        )
        if db_event.obj_recurence is not None:
            obj_event_recurente_service.delete_event_recurence(db_event.recurence_id, session)
        edited_event.recurence_id = db_event_recurence.id
        edited_event.obj_recurence = None

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

    if not verify_user_right_calendar(
        get_logged_user_context(), db_event.obj_calendar, "W"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    session.delete(db_event)
    session.commit()


def add_exception_event_recurence(event_id: str,  date: int, session: Session) -> None:
    """Permanently delete an event recurence.

    Requires at least "W" (Write) permission on the parent calendar.
    """

    db_event = session.get(ObjEventModel, event_id)
    if not db_event:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if not verify_user_right_calendar(
        get_logged_user_context(), db_event.obj_calendar, "W"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    return obj_event_recurente_service.add_exception_event_recurence(
        db_event.recurence_id,
        date,
        session
    )