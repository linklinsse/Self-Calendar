from typing import List
from fastapi import APIRouter

from app.services import lnk_user_calendar_service
from app.schemas.lnk_user_calendar_schema import (
    LnkUserCalendarSchemaComplete,
    LnkUserCalendarSchemaCreate,
    LnkUserCalendarSchemaEdit,
)

#TODO only loged user
router = APIRouter(prefix="/user_calendar")


@router.post("/", response_model=LnkUserCalendarSchemaComplete)
async def create(
    new_calendar: LnkUserCalendarSchemaCreate,
) -> LnkUserCalendarSchemaComplete:
    return lnk_user_calendar_service.create_lnk_user_calendar(
        new_calendar,
    )


@router.get("/all/{calendar_id}", response_model=List[LnkUserCalendarSchemaComplete])
async def get_all(calendar_id: str) -> List[LnkUserCalendarSchemaComplete]:
    return lnk_user_calendar_service.get_all_lnk_user_calendar(calendar_id)


@router.get("/{lnk_user_calendar_id}", response_model=LnkUserCalendarSchemaComplete)
async def get(lnk_user_calendar_id: str) -> LnkUserCalendarSchemaComplete:
    return lnk_user_calendar_service.get_calendar(
        lnk_user_calendar_id,
    )


@router.patch("/{lnk_user_calendar_id}", response_model=LnkUserCalendarSchemaComplete)
async def patch(
    lnk_user_calendar_id: str, edited_calendar: LnkUserCalendarSchemaEdit
) -> LnkUserCalendarSchemaComplete:
    return lnk_user_calendar_service.edit_calendar(
        lnk_user_calendar_id,
        edited_calendar,
    )


@router.delete("/{lnk_user_calendar_id}")
async def delete(lnk_user_calendar_id: str):
    return lnk_user_calendar_service.delete_calendar(
        lnk_user_calendar_id,
    )
