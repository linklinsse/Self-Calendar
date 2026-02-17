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
    db_calendar = ObjCalendarModel.model_validate(new_calendar)

    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)

    lnk_user_calendar = LnkUserCalendarSchemaCreate(
        user_id="test", calendar_id=db_calendar.id, right="O"
    )
    print(lnk_user_calendar)
    lnk_user_calendar_service.create_lnk_user_calendar(lnk_user_calendar)
    return db_calendar


@db_session_injector
def get_calendar(
    calendar_id: str, db_session: SessionDep
) -> ObjCalendarSchemaComplete:
    db_calendar = db_session.get(ObjCalendarModel, {"id": calendar_id})
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(get_loged_user_context(), db_calendar, 'C')

    if not has_right:
        raise HTTPException(status_code=404, detail="Calendar not found")

    return db_calendar

@db_session_injector
def get_all_calendar(db_session: SessionDep) -> List[ObjCalendarSchemaComplete]:
    loged_user = get_loged_user_context()

    return db_session.exec(
        select(ObjCalendarModel)
        .where(
            exists(LnkUserCalendarModel.id)
            .where(
                LnkUserCalendarModel.calendar_id == ObjCalendarModel.id
            )
            .where(
                LnkUserCalendarModel.user_id == loged_user.id
            )
        )
    ).all()


@db_session_injector
def edit_calendar(
    calendar_id: str,
    edited_calendar: ObjCalendarSchemaEdit,
    db_session: SessionDep,
) -> ObjCalendarSchemaComplete:
    db_calendar = db_session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(get_loged_user_context(), db_calendar, 'O')

    if not has_right:
        raise HTTPException(status_code=403, detail="No rihgt on Calendar")

    update_data = edited_calendar.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_calendar, key, value)

    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)

    return db_calendar


@db_session_injector
def delete_calendar(calendar_id: str, db_session: SessionDep):
    db_calendar = db_session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    has_right = verif_user_right_calendar(get_loged_user_context(), db_calendar, 'O')

    if not has_right:
        raise HTTPException(status_code=403, detail="No rihgt on Calendar")

    db_session.delete(db_calendar)
    db_session.commit()
