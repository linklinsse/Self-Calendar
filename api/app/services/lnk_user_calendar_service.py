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


# TODO verif right user on calender:
# If lenght == 0 no check
# Else check if Owner
@db_session_injector
def create_lnk_user_calendar(
    new_lnk_user_calendar: LnkUserCalendarSchemaCreate, db_session: SessionDep
) -> LnkUserCalendarSchemaComplete:
    db_calendar = LnkUserCalendarModel.model_validate(new_lnk_user_calendar)

    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)
    return db_calendar


@db_session_injector
def get_lnk_user_calendar(
    lnk_user_calendar_id: str, db_session: SessionDep
) -> LnkUserCalendarSchemaComplete:
    return db_session.get(LnkUserCalendarModel, lnk_user_calendar_id)


@db_session_injector
def get_all_lnk_user_calendar(
    calendar_id: str, db_session: SessionDep
) -> List[LnkUserCalendarSchemaComplete]:
    statement = select(LnkUserCalendarModel).where(
        LnkUserCalendarModel.calendar_id == calendar_id
    )
    results = db_session.exec(statement)
    list = results.all()
    return list


# TODO verif user owner > 1 SSI del owner
@db_session_injector
def edit_lnk_user_calendar(
    lnk_user_calendar_id: str,
    edited_lnk_user_calendar: LnkUserCalendarSchemaEdit,
    db_session: SessionDep,
) -> LnkUserCalendarSchemaComplete:
    db_lnk_user_calendar = db_session.get(
        LnkUserCalendarModel, lnk_user_calendar_id
    )
    if not db_lnk_user_calendar:
        raise HTTPException(status_code=404, detail="Right not found")

    update_data = edited_lnk_user_calendar.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_lnk_user_calendar, key, value)

    db_session.add(db_lnk_user_calendar)
    db_session.commit()
    db_session.refresh(db_lnk_user_calendar)

    return db_lnk_user_calendar


# TODO verif user owner > 1 SSI del owner
@db_session_injector
def delete_lnk_user_calendar(lnk_user_calendar_id: str, db_session: SessionDep):
    calendar = db_session.get(LnkUserCalendarModel, lnk_user_calendar_id)
    db_session.delete(calendar)
    db_session.commit()
