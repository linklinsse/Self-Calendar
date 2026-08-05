from sqlmodel import Session, select

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verify_user_right_calendar import verify_user_right_calendar
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_category_model import ObjCategoryModel
from app.models.obj_event_model import ObjEventModel
from app.schemas.obj_category_schema import ObjCategorySchemaCreate, ObjCategorySchemaEdit


def _get_calendar_or_404(calendar_id: str, session: Session) -> ObjCalendarModel:
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if db_calendar is None:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)
    return db_calendar


def create_category(
    new_category: ObjCategorySchemaCreate,
    session: Session,
) -> ObjCategoryModel:
    db_calendar = _get_calendar_or_404(new_category.calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "W"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    db_category = ObjCategoryModel.model_validate(new_category)

    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


def get_categories_by_calendar(
    calendar_id: str,
    session: Session,
) -> list[ObjCategoryModel]:
    db_calendar = _get_calendar_or_404(calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "R"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    statement = select(ObjCategoryModel).where(
        ObjCategoryModel.calendar_id == calendar_id
    )
    return list(session.exec(statement).all())


def get_category(
    category_id: str,
    session: Session,
) -> ObjCategoryModel:
    category = session.get(ObjCategoryModel, category_id)
    if category is None:
        raise_app_error(AppErrorCode.CATEGORY_NOT_FOUND)

    db_calendar = _get_calendar_or_404(category.calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "R"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    return category


def update_category(
    category_id: str,
    payload: ObjCategorySchemaEdit,
    session: Session,
) -> ObjCategoryModel:
    category = session.get(ObjCategoryModel, category_id)
    if category is None:
        raise_app_error(AppErrorCode.CATEGORY_NOT_FOUND)

    db_calendar = _get_calendar_or_404(category.calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "W"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    patch_data = payload.model_dump(exclude_unset=True)
    for key, value in patch_data.items():
        setattr(category, key, value)

    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(
    category_id: str,
    session: Session,
) -> None:
    category = session.get(ObjCategoryModel, category_id)
    if category is None:
        raise_app_error(AppErrorCode.CATEGORY_NOT_FOUND)

    db_calendar = _get_calendar_or_404(category.calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "W"):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    # Clear the references before deleting. ObjEventModel.category_id does
    # have a foreign key now (migration be83bce50e32), so the database would
    # reject the delete rather than leave orphans — but rejecting it is not
    # the behaviour we want: deleting a category the user no longer wants
    # should succeed and leave its events uncategorised, not fail because
    # something still uses it. Doing it here, in the same transaction, is
    # what makes that outcome possible.
    orphaned_events = session.exec(
        select(ObjEventModel).where(ObjEventModel.category_id == category_id)
    ).all()
    for db_event in orphaned_events:
        db_event.category_id = None
        session.add(db_event)

    session.delete(category)
    session.commit()
