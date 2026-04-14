from typing import List
from sqlmodel import Session, exists, select

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verify_user_right_calendar import verify_user_right_calendar
from app.models.lnk_user_calendar_model import LnkUserCalendarModel
from app.models.obj_calendar_model import ObjCalendarModel
from app.schemas.obj_calendar_schema import (
    ObjCalendarSchemaComplete,
    ObjCalendarSchemaCreate,
    ObjCalendarSchemaEdit,
)
from app.schemas.lnk_user_calendar_schema import LnkUserCalendarSchemaCreate
import app.services.lnk_user_calendar_service as lnk_user_calendar_service


def create_calendar(
    new_calendar: ObjCalendarSchemaCreate, session: Session
) -> ObjCalendarSchemaComplete:
    """Create a new calendar and assign the current user as its Owner.

    Both the calendar insert and the Owner membership insert share the same
    session, so they succeed or fail together.
    """
    db_calendar = ObjCalendarModel.model_validate(new_calendar)

    session.add(db_calendar)
    session.commit()
    session.refresh(db_calendar)

    logged_user = get_logged_user_context()
    lnk_user_calendar_service.create_lnk_user_calendar(
        LnkUserCalendarSchemaCreate(
            user_id=logged_user.id, calendar_id=db_calendar.id, right="O"
        ),
        session,
    )
    return db_calendar


def get_calendar(calendar_id: str, session: Session) -> ObjCalendarSchemaComplete:
    """Fetch a single calendar by ID.

    Returns 404 if the calendar does not exist OR if the current user has
    no access — this intentional ambiguity prevents calendar enumeration.
    Requires at least "R" (read) permission.
    """
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "R"):
        # Return 404 (not 403) to avoid leaking the calendar's existence.
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    return db_calendar


def get_all_calendar(session: Session) -> List[ObjCalendarSchemaComplete]:
    """Return all calendars the current user is linked to (any permission level)."""
    logged_user = get_logged_user_context()

    return session.exec(
        select(ObjCalendarModel).where(
            exists(LnkUserCalendarModel.id)
            .where(LnkUserCalendarModel.calendar_id == ObjCalendarModel.id)
            .where(LnkUserCalendarModel.user_id == logged_user.id)
        )
    ).all()


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

    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "O"):
        raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)

    update_data = edited_calendar.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_calendar, key, value)

    session.add(db_calendar)
    session.commit()
    session.refresh(db_calendar)

    return db_calendar


def delete_calendar(calendar_id: str, session: Session) -> None:
    """Permanently delete a calendar.

    Requires "O" (Owner) permission.
    TODO: Add cascade deletes for events and memberships (or rely on DB cascade).
    """
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "O"):
        raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)

    session.delete(db_calendar)
    session.commit()
