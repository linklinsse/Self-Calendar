
from datetime import datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select

from app.common.errors import AppErrorCode, raise_app_error
from app.models.obj_event_recurence_model import ObjEventRecurenceModel
from app.schemas.obj_event_recurence_schema import ObjEventRecurenceSchemaCreate
from app.models.obj_event_recurence_exception_model import ObjEventRecurenceExceptionModel

def create_event_recurence(
    new_recurence: ObjEventRecurenceSchemaCreate,
    date_start: int,
    session: Session,
) -> ObjEventRecurenceModel:
    db_recurence = ObjEventRecurenceModel.model_validate(new_recurence)
    db_recurence.estimated_end_date = compute_estimated_end(db_recurence, date_start)
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

# The fields that actually define a recurrence rule. `estimated_end_date` is
# derived (see compute_estimated_end) and `id` / exceptions are not part of
# the rule itself, so neither participates in the comparison.
_RULE_FIELDS = ("type", "interval", "days", "endType", "count", "until")


def recurrence_rules_match(db_recurence, incoming) -> bool:
    """True when an incoming recurrence payload describes the rule already
    stored on the event.

    Clients that always serialise the whole event (the web app does) resend
    the recurrence on every PATCH, including edits that only touch the title.
    Treating that as a replacement destroys the rule's exception rows, so the
    service needs to be able to tell "echoed back unchanged" from "the user
    actually changed the recurrence".
    """
    if db_recurence is None or incoming is None:
        return False
    return all(
        getattr(db_recurence, field) == getattr(incoming, field, None)
        for field in _RULE_FIELDS
    )


def refresh_estimated_end(
    db_recurence: ObjEventRecurenceModel,
    date_start: int,
    session: Session,
) -> None:
    """Recompute estimated_end_date in place.

    The rule can be unchanged while the event's start moves, and
    estimated_end_date is derived from both (it drives the recurring-event
    branch of get_all_event_between's range filter).
    """
    new_end = compute_estimated_end(db_recurence, date_start)
    if new_end != db_recurence.estimated_end_date:
        db_recurence.estimated_end_date = new_end
        session.add(db_recurence)
        session.commit()
        session.refresh(db_recurence)


def copy_exceptions(
    source: ObjEventRecurenceModel,
    target: ObjEventRecurenceModel,
    session: Session,
) -> None:
    """Re-point a rule's excluded occurrence dates at a replacement rule.

    When the user genuinely edits a recurrence, the old row is deleted and a
    new one takes its place. Dropping the exceptions along with it means every
    occurrence they had individually deleted silently reappears.
    """
    for db_exception in list(source.obj_exceptions):
        session.add(
            ObjEventRecurenceExceptionModel(
                recurrence_id=target.id, date=db_exception.date
            )
        )
    session.commit()


def delete_event_recurence(
    recurence_id: str,
    session: Session,
) -> None:
    recurence = session.get(ObjEventRecurenceModel, recurence_id)
    if recurence is None:
        raise_app_error(AppErrorCode.RECURRENCE_NOT_FOUND)

    # recurrence_id on the exception rows is NOT NULL, so these must be
    # removed before the recurrence itself (see delete_calendar for the
    # same pattern / rationale).
    for db_exception in list(recurence.obj_exceptions):
        session.delete(db_exception)

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
    dt = datetime.fromtimestamp(date_start, tz=timezone.utc)
    n = recurrence.count * recurrence.interval  # total units to advance

    match recurrence.type:
        case 'D':
            dt += timedelta(days=n)
        case 'W':
            dt += timedelta(weeks=n)
        case 'M':
            dt += relativedelta(months=n)
        case 'Y':
            dt += relativedelta(years=n)

    return int(dt.timestamp())
