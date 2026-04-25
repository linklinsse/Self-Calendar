
from sqlmodel import Session, select
from datetime import datetime

from app.models.obj_event_recurence_model import ObjEventRecurenceModel
from app.schemas.obj_event_recurence_schema import ObjEventRecurenceSchemaCreate, ObjEventRecurenceSchemaEdit
from app.models.obj_event_recurence_exception_model import ObjEventRecurenceExceptionModel

def create_event_recurence(
    new_recurence: ObjEventRecurenceSchemaCreate,
    date_start: int,
    session: Session,
) -> ObjEventRecurenceModel:
    db_recurence = ObjEventRecurenceModel.model_validate(new_recurence)
    db_recurence.estimated_end_date = compute_estimated_end(ObjEventRecurenceModel, date_start)
    session.add(db_recurence)
    session.commit()
    session.refresh(db_recurence)
    return db_recurence

# Not used right now
# def update_event_recurence(
#     updated_recurence: ObjEventRecurenceSchemaEdit,
#     session: Session,
# ) -> ObjEventRecurenceModel:
#     recurence = session.get(ObjEventRecurenceModel, recurence_id)
#     if recurence is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Recurence not found",
#         )

#     patch_data = updated_recurence.model_dump(exclude_unset=True)
#     for key, value in patch_data.items():
#         setattr(recurence, key, value)

#     session.add(recurence)
#     session.commit()
#     session.refresh(recurence)
#     return recurence

def delete_event_recurence(
    recurence_id: str,
    session: Session,
) -> None:
    recurence = session.get(ObjEventRecurenceModel, recurence_id)
    if recurence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurence not found",
        )

    session.delete(recurence)
    session.commit()

def add_exception_event_recurence(
    recurrence_id: str,
    date: int,
    session: Session
) -> ObjEventRecurenceExceptionModel:
    already_exists = session.exec(
        select(ObjEventRecurenceExceptionModel).where(
            ObjEventRecurenceExceptionModel.recurrence_id == recurrence_id,
            ObjEventRecurenceExceptionModel.date == date,
        )
    ).first()

    if already_exists:
        return already_exists

    db_exception = ObjEventRecurenceExceptionModel(recurrence_id=recurrence_id, date=date)
    session.add(db_exception)
    session.commit()
    session.refresh(db_exception)
    return db_exception

def compute_estimated_end(
    recurrence: ObjEventRecurenceModel,
    date_start: int
) -> int | None:
    if recurrence.endType == 'N':
        return None
    if recurrence.endType == 'U':
        return recurrence.until

    # endType == 'C'
    dt = datetime.fromtimestamp(date_start)
    n = recurrence.count * recurrence.interval  # total units to advance

    match recurrence.type:
        case 'D': dt += timedelta(days=n)
        case 'W': dt += timedelta(weeks=n)
        case 'M': dt += relativedelta(months=n)
        case 'Y': dt += relativedelta(years=n)

    return int(dt.timestamp())
