from typing import List
from fastapi import APIRouter

from app.services import obj_calendar_service
from app.schemas.obj_calendar_schema import (
    ObjCalendarSchemaComplete,
    ObjCalendarSchemaCreate,
    ObjCalendarSchemaEdit,
)

router = APIRouter(prefix="/calendar")


@router.post("/", response_model=ObjCalendarSchemaComplete)
async def create(
    new_calendar: ObjCalendarSchemaCreate,
) -> ObjCalendarSchemaComplete:
    """Create a new calendar. The authenticated user becomes its Owner."""
    return obj_calendar_service.create_calendar(new_calendar)


@router.get("/", response_model=List[ObjCalendarSchemaComplete])
async def get_all() -> List[ObjCalendarSchemaComplete]:
    """Return all calendars the authenticated user has access to."""
    return obj_calendar_service.get_all_calendar()


@router.get("/{calendar_id}", response_model=ObjCalendarSchemaComplete)
async def get(calendar_id: str) -> ObjCalendarSchemaComplete:
    """Return a single calendar. Requires at least read ("R") permission."""
    return obj_calendar_service.get_calendar(calendar_id)


@router.patch("/{calendar_id}", response_model=ObjCalendarSchemaComplete)
async def patch(
    calendar_id: str, edited_calendar: ObjCalendarSchemaEdit
) -> ObjCalendarSchemaComplete:
    """Update a calendar's metadata. Requires Owner ("O") permission."""
    return obj_calendar_service.edit_calendar(calendar_id, edited_calendar)


@router.delete("/{calendar_id}")
async def delete(calendar_id: str):
    """Permanently delete a calendar. Requires Owner ("O") permission."""
    return obj_calendar_service.delete_calendar(calendar_id)
