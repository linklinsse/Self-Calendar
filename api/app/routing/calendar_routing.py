from typing import List
from fastapi import APIRouter

from app.services import obj_calendar_service
from app.schemas.obj_calendar_schema import (
    ObjCalendarSchemaComplete,
    ObjCalendarSchemaCreate,
    ObjCalendarSchemaEdit,
)

# TODO only loged user
router = APIRouter(prefix="/calendar")


@router.post("/", response_model=ObjCalendarSchemaComplete)
async def create(
    new_calendar: ObjCalendarSchemaCreate,
) -> ObjCalendarSchemaComplete:
    return obj_calendar_service.create_calendar(
        new_calendar,
    )


@router.get("/", response_model=List[ObjCalendarSchemaComplete])
async def get_all() -> List[ObjCalendarSchemaComplete]:
    return obj_calendar_service.get_all_calendar()


@router.get("/{calendar_id}", response_model=ObjCalendarSchemaComplete)
async def get(calendar_id: str) -> ObjCalendarSchemaComplete:
    return obj_calendar_service.get_calendar(
        calendar_id,
    )


@router.patch("/{calendar_id}", response_model=ObjCalendarSchemaComplete)
async def patch(
    calendar_id: str, edited_calendar: ObjCalendarSchemaEdit
) -> ObjCalendarSchemaComplete:
    return obj_calendar_service.edit_calendar(
        calendar_id,
        edited_calendar,
    )


@router.delete("/{calendar_id}")
async def delete(calendar_id: str):
    return obj_calendar_service.delete_calendar(
        calendar_id,
    )
