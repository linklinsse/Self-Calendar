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
    db_calendar = db_session.get(
        ObjCalendarModel, {"id": new_event.calendar_id}
    )
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
    db_calendar = db_session.get(ObjCalendarModel, {"id": calendar_id})
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

    if category_id is not None:
        statement = statement.where(ObjEventModel.category_id == category_id)

    results = db_session.exec(statement)
    list = results.all()
    return list


@db_session_injector
def get_event(event_id: str, db_session: SessionDep) -> ObjEventSchemaComplete:
    db_event = db_session.get(ObjEventModel, {"id": event_id})
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
    db_event = db_session.get(ObjEventModel, {"id": event_id})
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "P"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = edited_event.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    db_session.add(db_event)
    db_session.commit()
    db_session.refresh(db_event)

    return db_event


@db_session_injector
def delete_event(event_id: str, db_session: SessionDep):
    db_event = db_session.get(ObjEventModel, {"id": event_id})
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    has_right = verif_user_right_calendar(
        get_loged_user_context(), db_event.obj_calendar, "P"
    )
    if not has_right:
        raise HTTPException(status_code=404, detail="Event not found")

    db_session.delete(db_event)
    db_session.commit()
