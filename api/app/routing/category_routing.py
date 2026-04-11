from fastapi import APIRouter, Depends

from app.common.db_connection import SessionDep
from app.common.dependencies.verify_loged_user_dependency import (
    verify_loged_user_dependency,
)
from app.schemas.obj_category_schema import (
    ObjCategoryCreate,
    ObjCategoryRead,
    ObjCategoryUpdate,
)
from app.services.obj_category_service import (
    create_category,
    delete_category,
    get_categories_by_calendar,
    get_category,
    update_category,
)

router = APIRouter(
    prefix="/category",
    tags=["category"],
)


@router.post("/", response_model=ObjCategoryRead, status_code=201)
def route_create_category(
    payload: ObjCategoryCreate,
    session: SessionDep,
) -> ObjCategoryRead:
    return create_category(new_category=payload, session=session)


@router.get(
    "/calendar/{calendar_id}",
    response_model=list[ObjCategoryRead],
)
def route_get_categories_by_calendar(
    calendar_id: str,
    session: SessionDep,
) -> list[ObjCategoryRead]:
    return get_categories_by_calendar(
        calendar_id=calendar_id,
        session=session,
    )


@router.get("/{category_id}", response_model=ObjCategoryRead)
def route_get_category(
    category_id: str,
    session: SessionDep,
) -> ObjCategoryRead:
    return get_category(category_id=category_id, session=session)


@router.patch("/{category_id}", response_model=ObjCategoryRead)
def route_update_category(
    category_id: str,
    payload: ObjCategoryUpdate,
    session: SessionDep,
) -> ObjCategoryRead:
    return update_category(
        category_id=category_id,
        payload=payload,
        session=session,
    )


@router.delete("/{category_id}", status_code=204)
def route_delete_category(
    category_id: str,
    session: SessionDep,
) -> None:
    delete_category(category_id=category_id, session=session)
