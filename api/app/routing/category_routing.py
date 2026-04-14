from fastapi import APIRouter

from app.common.db_connection import SessionDep
from app.schemas.obj_category_schema import (
    ObjCategorySchemaCreate,
    ObjCategorySchemaComplete,
    ObjCategorySchemaEdit,
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


@router.post("/", response_model=ObjCategorySchemaComplete, status_code=201)
def create(
    payload: ObjCategorySchemaCreate,
    session: SessionDep,
) -> ObjCategorySchemaComplete:
    return create_category(new_category=payload, session=session)


@router.get(
    "/calendar/{calendar_id}",
    response_model=list[ObjCategorySchemaComplete],
)
def get_all(
    calendar_id: str,
    session: SessionDep,
) -> list[ObjCategorySchemaComplete]:
    return get_categories_by_calendar(
        calendar_id=calendar_id,
        session=session,
    )


@router.get("/{category_id}", response_model=ObjCategorySchemaComplete)
def get(
    category_id: str,
    session: SessionDep,
) -> ObjCategorySchemaComplete:
    return get_category(category_id=category_id, session=session)


@router.patch("/{category_id}", response_model=ObjCategorySchemaComplete)
def patch(
    category_id: str,
    payload: ObjCategorySchemaEdit,
    session: SessionDep,
) -> ObjCategorySchemaComplete:
    return update_category(
        category_id=category_id,
        payload=payload,
        session=session,
    )


@router.delete("/{category_id}", status_code=204)
def delete(
    category_id: str,
    session: SessionDep,
) -> None:
    delete_category(category_id=category_id, session=session)
