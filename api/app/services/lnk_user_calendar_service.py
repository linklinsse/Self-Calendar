from typing import List
from sqlmodel import select
from fastapi import HTTPException

from app.common.decorators.db_session_injector import db_session_injector
from app.schemas.lnk_user_calendar_schema import (
    LnkUserCalendarSchemaComplete,
    LnkUserCalendarSchemaCreate,
    LnkUserCalendarSchemaEdit,
)
from app.models.lnk_user_calendar_model import LnkUserCalendarModel
from app.common.db_connection import SessionDep


# TODO: add permission checks before mutating link records:
#   - On create: if there are already members, verify the caller is an Owner.
#   - On edit/delete: verify the caller is an Owner.
#   - On delete: prevent removing the last Owner of a calendar.


@db_session_injector
def create_lnk_user_calendar(
    new_lnk_user_calendar: LnkUserCalendarSchemaCreate, db_session: SessionDep
) -> LnkUserCalendarSchemaComplete:
    """Create a new user–calendar membership record.

    The caller is responsible for verifying that the current user is authorised
    to add members before calling this function (see TODO above).
    """
    db_link = LnkUserCalendarModel.model_validate(new_lnk_user_calendar)

    db_session.add(db_link)
    db_session.commit()
    db_session.refresh(db_link)
    return db_link


@db_session_injector
def get_lnk_user_calendar(
    lnk_user_calendar_id: str, db_session: SessionDep
) -> LnkUserCalendarSchemaComplete:
    """Fetch a single user–calendar membership record by its ID."""
    return db_session.get(LnkUserCalendarModel, lnk_user_calendar_id)


@db_session_injector
def get_all_lnk_user_calendar(
    calendar_id: str, db_session: SessionDep
) -> List[LnkUserCalendarSchemaComplete]:
    """Return all membership records for a given calendar."""
    statement = select(LnkUserCalendarModel).where(
        LnkUserCalendarModel.calendar_id == calendar_id
    )
    results = db_session.exec(statement)
    return results.all()


@db_session_injector
def edit_lnk_user_calendar(
    lnk_user_calendar_id: str,
    edited_lnk_user_calendar: LnkUserCalendarSchemaEdit,
    db_session: SessionDep,
) -> LnkUserCalendarSchemaComplete:
    """Update the permission level on an existing user–calendar membership.

    Only fields provided in the request body are modified (PATCH semantics).
    TODO: Prevent demoting / removing the last Owner of a calendar.
    """
    db_link = db_session.get(LnkUserCalendarModel, lnk_user_calendar_id)
    if not db_link:
        raise HTTPException(status_code=404, detail="Right not found")

    update_data = edited_lnk_user_calendar.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_link, key, value)

    db_session.add(db_link)
    db_session.commit()
    db_session.refresh(db_link)

    return db_link


@db_session_injector
def delete_lnk_user_calendar(lnk_user_calendar_id: str, db_session: SessionDep):
    """Remove a user–calendar membership record.

    TODO: Prevent deleting the last Owner membership of a calendar.
    """
    db_link = db_session.get(LnkUserCalendarModel, lnk_user_calendar_id)
    if not db_link:
        raise HTTPException(status_code=404, detail="Right not found")
    db_session.delete(db_link)
    db_session.commit()
