from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.utils.verify_user_right_calendar import verify_user_right_calendar
from app.models.obj_category_model import ObjCategoryModel
from app.schemas.obj_category_schema import ObjCategorySchemaCreate, ObjCategorySchemaEdit


def create_category(
    new_category: ObjCategorySchemaCreate,
    session: Session,
) -> ObjCategoryModel:
    # TODO fix it
    # verify_user_right_calendar(
    #     user_id=get_logged_user_context()
    #     calendar_id=payload.calendar_id,
    #     required_right="W",
    # )

    db_category = ObjCategoryModel.model_validate(new_category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


def get_categories_by_calendar(
    calendar_id: str,
    session: Session,
) -> list[ObjCategoryModel]:
    # TODO fix it
    # verify_user_right_calendar(
    #     user_id=get_logged_user_context()
    #     calendar_id=payload.calendar_id,
    #     required_right="R",
    # )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # TODO fix it
    # verify_user_right_calendar(
    #     user_id=get_logged_user_context()
    #     calendar_id=payload.calendar_id,
    #     required_right="R",
    # )

    return category


def update_category(
    category_id: str,
    payload: ObjCategorySchemaEdit,
    session: Session,
) -> ObjCategoryModel:
    category = session.get(ObjCategoryModel, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # TODO fix it
    # verify_user_right_calendar(
    #     user_id=get_logged_user_context()
    #     calendar_id=payload.calendar_id,
    #     required_right="W",
    # )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # TODO fix it
    # verify_user_right_calendar(
    #     user_id=get_logged_user_context()
    #     calendar_id=payload.calendar_id,
    #     required_right="W",
    # )

    session.delete(category)
    session.commit()
