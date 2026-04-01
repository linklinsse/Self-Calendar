from typing import List
from fastapi import APIRouter

from app.services import lnk_user_calendar_service
from app.schemas.lnk_user_calendar_schema import (
    LnkUserCalendarSchemaComplete,
    LnkUserCalendarSchemaCreate,
    LnkUserCalendarSchemaEdit,
)

router = APIRouter(prefix="/user_calendar")


@router.post("/", response_model=LnkUserCalendarSchemaComplete)
async def create(
    new_calendar: LnkUserCalendarSchemaCreate,
) -> LnkUserCalendarSchemaComplete:
    """Create a new user–calendar membership."""
    return lnk_user_calendar_service.create_lnk_user_calendar(
        new_calendar,
    )


@router.get(
    "/all/{calendar_id}", response_model=List[LnkUserCalendarSchemaComplete]
)
async def get_all(calendar_id: str) -> List[LnkUserCalendarSchemaComplete]:
    """List all members of a calendar."""
    return lnk_user_calendar_service.get_all_lnk_user_calendar(calendar_id)


@router.get(
    "/{lnk_user_calendar_id}", response_model=LnkUserCalendarSchemaComplete
)
async def get(lnk_user_calendar_id: str) -> LnkUserCalendarSchemaComplete:
    """Get a single user–calendar membership by ID."""
    return lnk_user_calendar_service.get_lnk_user_calendar(
        lnk_user_calendar_id,
    )


@router.patch(
    "/{lnk_user_calendar_id}", response_model=LnkUserCalendarSchemaComplete
)
async def patch(
    lnk_user_calendar_id: str, edited_calendar: LnkUserCalendarSchemaEdit
) -> LnkUserCalendarSchemaComplete:
    """Update the permission level of an existing membership."""
    return lnk_user_calendar_service.edit_lnk_user_calendar(
        lnk_user_calendar_id,
        edited_calendar,
    )


@router.delete("/{lnk_user_calendar_id}")
async def delete(lnk_user_calendar_id: str):
    """Remove a user from a calendar."""
    return lnk_user_calendar_service.delete_lnk_user_calendar(
        lnk_user_calendar_id,
    )
