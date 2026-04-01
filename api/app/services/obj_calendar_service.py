from typing import List
from sqlmodel import exists, select
from fastapi import HTTPException

from app.common.contexts.loged_user_context import get_loged_user_context
from app.common.decorators.db_session_injector import db_session_injector
from app.common.utils.verif_user_right_calendar import verif_user_right_calendar
from app.models.lnk_user_calendar_model import LnkUserCalendarModel
from app.schemas.obj_calendar_schema import (
    ObjCalendarSchemaComplete,
    ObjCalendarSchemaCreate,
    ObjCalendarSchemaEdit,
)
from app.models.obj_calendar_model import ObjCalendarModel
from app.common.db_connection import SessionDep
from app.schemas.lnk_user_calendar_schema import (
    LnkUserCalendarSchemaCreate,
)

import app.services.lnk_user_calendar_service as lnk_user_calendar_service


@db_session_injector
def create_calendar(
    new_calendar: ObjCalendarSchemaCreate, db_session: SessionDep
) -> ObjCalendarSchemaComplete:
    """Create a new calendar and assign the current user as its Owner.

    The creator is automatically linked to the calendar with right "O" (Owner),
    which grants full control (edit, delete, manage members).
    """
    db_calendar = ObjCalendarModel.model_validate(new_calendar)

    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)

    loged_user = get_loged_user_context()
    lnk_user_calendar = LnkUserCalendarSchemaCreate(
        user_id=loged_user.id, calendar_id=db_calendar.id, right="O"
    )
    lnk_user_calendar_service.create_lnk_user_calendar(lnk_user_calendar)
    return db_calendar


@db_session_injector
def get_calendar(
    calendar_id: str, db_session: SessionDep
) -> ObjCalendarSchemaComplete:
    """Fetch a single calendar by ID.

    Returns 404 if the calendar does not exist OR if the current user has
    no access — this intentional ambiguity prevents calendar enumeration.
    Requires at least "C" (Consulter / read) permission.
    """
    db_calendar = db_session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_calendar, "C"
    )
    if not has_right:
        # Return 404 (not 403) to avoid leaking the calendar's existence
        raise HTTPException(status_code=404, detail="Calendar not found")

    return db_calendar


@db_session_injector
def get_all_calendar(db_session: SessionDep) -> List[ObjCalendarSchemaComplete]:
    """Return all calendars the current user is linked to (any permission level)."""
    loged_user = get_loged_user_context()

    # Use an EXISTS subquery to filter calendars that have a matching
    # lnk_user_calendar row for the current user
    return db_session.exec(
        select(ObjCalendarModel).where(
            exists(LnkUserCalendarModel.id)
            .where(LnkUserCalendarModel.calendar_id == ObjCalendarModel.id)
            .where(LnkUserCalendarModel.user_id == loged_user.id)
        )
    ).all()


@db_session_injector
def edit_calendar(
    calendar_id: str,
    edited_calendar: ObjCalendarSchemaEdit,
    db_session: SessionDep,
) -> ObjCalendarSchemaComplete:
    """Update a calendar's fields.

    Requires "O" (Owner) permission.
    Only fields present in the request body are updated (PATCH semantics).
    """
    db_calendar = db_session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_calendar, "O"
    )
    if not has_right:
        raise HTTPException(status_code=403, detail="No right on Calendar")

    # Apply only the fields that were explicitly provided in the request body
    update_data = edited_calendar.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_calendar, key, value)

    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)

    return db_calendar


@db_session_injector
def delete_calendar(calendar_id: str, db_session: SessionDep):
    """Permanently delete a calendar.

    Requires "O" (Owner) permission.
    TODO: Cascade-delete linked events and user links, or rely on DB cascade.
    """
    db_calendar = db_session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_calendar, "O"
    )
    if not has_right:
        raise HTTPException(status_code=403, detail="No right on Calendar")

    db_session.delete(db_calendar)
    db_session.commit()
