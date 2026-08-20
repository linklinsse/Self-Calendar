from typing import List
from sqlalchemy.orm import selectinload
from sqlmodel import Session, exists, select

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verify_user_right_calendar import (
    require_calendar_right,
    verify_user_right_calendar,
)
from app.models.lnk_user_calendar_model import LnkUserCalendarModel
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_category_model import ObjCategoryModel
from app.schemas.obj_calendar_schema import (
    ObjCalendarSchemaComplete,
    ObjCalendarSchemaCreate,
    ObjCalendarSchemaEdit,
)
import app.services.lnk_user_calendar_service as lnk_user_calendar_service


def _to_schema(
    db_calendar: ObjCalendarModel, user_right: str | None
) -> ObjCalendarSchemaComplete:
    """Convert an ORM calendar to the response schema, attaching the
    current user's permission level (see ObjCalendarModel.user_right)."""
    return ObjCalendarSchemaComplete(
        id=db_calendar.id,
        title=db_calendar.title,
        description=db_calendar.description,
        color=db_calendar.color,
        user_right=user_right,
    )


def _resolve_user_right(db_calendar: ObjCalendarModel, user_id: str) -> str | None:
    """Return the calling user's right on this calendar, or None if unlinked."""
    for db_lnk in db_calendar.lnk_users:
        if db_lnk.user_id == user_id:
            return db_lnk.right
    return None


def create_calendar(
    new_calendar: ObjCalendarSchemaCreate, session: Session
) -> ObjCalendarSchemaComplete:
    """Create a new calendar and assign the current user as its Owner.

    The calendar insert and the Owner membership insert are only flushed
    (not committed) until both have succeeded, then committed together in a
    single transaction — so they truly succeed or fail together.
    """
    db_calendar = ObjCalendarModel.model_validate(new_calendar)

    session.add(db_calendar)
    session.flush()
    session.refresh(db_calendar)

    logged_user = get_logged_user_context()
    lnk_user_calendar_service._create_link_unchecked(
        logged_user.id, db_calendar.id, "O", session
    )
    session.commit()
    session.refresh(db_calendar)

    # The creator is always assigned Owner above, so no need to re-query it.
    return _to_schema(db_calendar, "O")


def get_calendar(calendar_id: str, session: Session) -> ObjCalendarSchemaComplete:
    """Fetch a single calendar by ID.

    Returns 404 if the calendar does not exist OR if the current user has
    no access — this intentional ambiguity prevents calendar enumeration.
    Requires at least "R" (read) permission.
    """
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    logged_user = get_logged_user_context()
    if not verify_user_right_calendar(logged_user, db_calendar, "R"):
        # Return 404 (not 403) to avoid leaking the calendar's existence.
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    return _to_schema(db_calendar, _resolve_user_right(db_calendar, logged_user.id))


def get_all_calendar(session: Session) -> List[ObjCalendarSchemaComplete]:
    """Return all calendars the current user is linked to (any permission level)."""
    logged_user = get_logged_user_context()

    db_calendars = session.exec(
        select(ObjCalendarModel)
        .where(
            exists(LnkUserCalendarModel.id)
            .where(LnkUserCalendarModel.calendar_id == ObjCalendarModel.id)
            .where(LnkUserCalendarModel.user_id == logged_user.id)
        )
        .options(selectinload(ObjCalendarModel.lnk_users))
    ).all()

    return [
        _to_schema(db_calendar, _resolve_user_right(db_calendar, logged_user.id))
        for db_calendar in db_calendars
    ]


def edit_calendar(
    calendar_id: str,
    edited_calendar: ObjCalendarSchemaEdit,
    session: Session,
) -> ObjCalendarSchemaComplete:
    """Update a calendar's fields.

    Requires "O" (Owner) permission.
    Only fields present in the request body are updated (PATCH semantics).
    """
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    require_calendar_right(get_logged_user_context(), db_calendar, "O")

    update_data = edited_calendar.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_calendar, key, value)

    session.add(db_calendar)
    session.commit()
    session.refresh(db_calendar)

    # Editing already required Owner permission above.
    return _to_schema(db_calendar, "O")


def delete_calendar(calendar_id: str, session: Session) -> None:
    """Permanently delete a calendar and everything scoped to it.

    Requires "O" (Owner) permission.

    SQLModel/SQLAlchemy's default relationship behavior tries to NULL out
    child foreign keys before deleting the parent; since calendar_id (and
    recurrence_id, on the exceptions) are NOT NULL columns, deleting a
    calendar without first removing its dependents raises an IntegrityError.
    So this explicitly deletes events (+ their recurrences/exceptions),
    categories, and memberships before deleting the calendar itself.
    """
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    require_calendar_right(get_logged_user_context(), db_calendar, "O")

    for db_event in list(db_calendar.obj_events):
        if db_event.obj_recurence is not None:
            for db_exception in list(db_event.obj_recurence.obj_exceptions):
                session.delete(db_exception)
            session.delete(db_event.obj_recurence)
        session.delete(db_event)

    db_categories = session.exec(
        select(ObjCategoryModel).where(ObjCategoryModel.calendar_id == calendar_id)
    ).all()
    for db_category in db_categories:
        session.delete(db_category)

    for db_lnk in list(db_calendar.lnk_users):
        session.delete(db_lnk)

    session.delete(db_calendar)
    session.commit()
