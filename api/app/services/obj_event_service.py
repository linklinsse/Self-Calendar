from typing import List
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, and_, or_

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verify_user_right_calendar import verify_user_right_calendar
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_category_model import ObjCategoryModel
from app.models.obj_event_model import ObjEventModel
from app.models.obj_event_recurence_model import ObjEventRecurenceModel
from app.schemas.obj_event_schema import (
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)
from app.services import obj_event_recurente_service



def _validate_category_in_calendar(
    category_id: str | None, calendar_id: str, session: Session
) -> None:
    """A category attached to an event must belong to the event's own
    calendar — otherwise a write-access user on calendar A could attach a
    category from calendar B, leaking its title/color into A's responses."""
    if category_id is None:
        return
    db_category = session.get(ObjCategoryModel, category_id)
    if db_category is None or db_category.calendar_id != calendar_id:
        raise_app_error(AppErrorCode.CATEGORY_NOT_FOUND)


def _validate_date_range(date_start: int, date_end: int) -> None:
    if date_end < date_start:
        raise_app_error(AppErrorCode.INVALID_DATE_RANGE)


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

    _validate_category_in_calendar(new_event.category_id, new_event.calendar_id, session)
    _validate_date_range(new_event.date_start, new_event.date_end)

    db_event_recurence = None
    if new_event.obj_recurence is not None:
        db_event_recurence = obj_event_recurente_service.create_event_recurence(
            new_event.obj_recurence,
            new_event.date_start,
            session
        )

    # `obj_recurence` is the nested *request* schema, not an ORM row —
    # feeding it to model_validate would try to assign it straight into the
    # relationship attribute. The recurrence is linked by id below instead.
    db_event = ObjEventModel.model_validate(
        new_event.model_dump(exclude={"obj_recurence"})
    )

    # recurence_id is set here, from the row we just created — never from the
    # request body (see ObjEventSchemaCreate's docstring).
    if db_event_recurence is not None:
        db_event.recurence_id = db_event_recurence.id

    session.add(db_event)
    session.commit()
    session.refresh(db_event)

    return db_event


def get_all_event_between(
    calendar_ids: List[str],
    from_date: int | None,
    to_date: int | None,
    category_ids: str | None,
    limit: int,
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
        limit:        Max number of rows returned.
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
    ).options(
        selectinload(ObjEventModel.obj_recurence).selectinload(
            ObjEventRecurenceModel.obj_exceptions
        )
    )

    if category_ids is not None:
        statement = statement.where(ObjEventModel.category_id.in_(category_ids))

    statement = statement.limit(limit)

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

    if "category_id" in edited_event.model_fields_set:
        _validate_category_in_calendar(
            edited_event.category_id, db_event.calendar_id, session
        )

    if "date_start" in edited_event.model_fields_set or "date_end" in edited_event.model_fields_set:
        effective_start = (
            edited_event.date_start
            if edited_event.date_start is not None
            else db_event.date_start
        )
        effective_end = (
            edited_event.date_end
            if edited_event.date_end is not None
            else db_event.date_end
        )
        _validate_date_range(effective_start, effective_end)

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

        if obj_event_recurente_service.recurrence_rules_match(
            db_event.obj_recurence, edited_event.obj_recurence
        ):
            # Identical rule — the client is just echoing back what it read
            # (event.service.js's serialise() always sends the full payload,
            # so *every* edit of a recurring event lands here). Replacing the
            # row would drop all of its exception records, silently undoing
            # every occurrence the user had individually deleted.
            obj_event_recurente_service.refresh_estimated_end(
                db_event.obj_recurence, recurence_date_start, session
            )
        else:
            db_event_recurence = obj_event_recurente_service.create_event_recurence(
                edited_event.obj_recurence,
                recurence_date_start,
                session
            )
            old_recurence = db_event.obj_recurence
            # Carry the user's per-occurrence exclusions over to the new rule
            # rather than discarding them.
            if old_recurence is not None:
                obj_event_recurente_service.copy_exceptions(
                    old_recurence, db_event_recurence, session
                )
            # Set on the ORM row directly — recurence_id is not a field on
            # the request schema (see ObjEventSchemaCreate's docstring).
            db_event.recurence_id = db_event_recurence.id
            if old_recurence is not None:
                obj_event_recurente_service.delete_event_recurence(
                    old_recurence.id, session
                )

    update_data = edited_event.model_dump(exclude_unset=True, exclude={"obj_recurence"})
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

    # recurence_id on the recurrence (and recurrence_id on its exceptions)
    # are NOT NULL, so these must go before the event — same pattern as
    # delete_calendar.
    if db_event.obj_recurence is not None:
        for db_exception in list(db_event.obj_recurence.obj_exceptions):
            session.delete(db_exception)
        session.delete(db_event.obj_recurence)

    session.delete(db_event)
    session.commit()


def add_exception_event_recurence(event_id: str,  date: int, session: Session) -> None:
    """Exclude one occurrence date from a recurring event.

    Requires at least "W" (Write) permission on the parent calendar.
    Raises 404 (EVENT_NOT_FOUND) if the event isn't a recurring event —
    recurence_id is NOT NULL on the exception table, so passing None
    through would otherwise raise an IntegrityError (500).
    """

    db_event = session.get(ObjEventModel, event_id)
    if not db_event:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if not verify_user_right_calendar(
        get_logged_user_context(), db_event.obj_calendar, "W"
    ):
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    if db_event.recurence_id is None:
        raise_app_error(AppErrorCode.EVENT_NOT_FOUND)

    return obj_event_recurente_service.add_exception_event_recurence(
        db_event.recurence_id,
        date,
        session
    )