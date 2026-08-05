from typing import List
from fastapi import APIRouter

from app.common.db_connection import SessionDep
from app.services import obj_calendar_service
from app.schemas.obj_calendar_schema import (
    ObjCalendarSchemaComplete,
    ObjCalendarSchemaCreate,
    ObjCalendarSchemaEdit,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/", response_model=ObjCalendarSchemaComplete)
def create(
    new_calendar: ObjCalendarSchemaCreate, session: SessionDep
) -> ObjCalendarSchemaComplete:
    """Create a new calendar. The authenticated user becomes its Owner."""
    return obj_calendar_service.create_calendar(new_calendar, session)


@router.get("/", response_model=List[ObjCalendarSchemaComplete])
def get_all(session: SessionDep) -> List[ObjCalendarSchemaComplete]:
    """Return all calendars the authenticated user has access to."""
    return obj_calendar_service.get_all_calendar(session)


@router.get("/{calendar_id}", response_model=ObjCalendarSchemaComplete)
def get(calendar_id: str, session: SessionDep) -> ObjCalendarSchemaComplete:
    """Return a single calendar. Requires at least read ("R") permission."""
    return obj_calendar_service.get_calendar(calendar_id, session)


@router.patch("/{calendar_id}", response_model=ObjCalendarSchemaComplete)
def patch(
    calendar_id: str, edited_calendar: ObjCalendarSchemaEdit, session: SessionDep
) -> ObjCalendarSchemaComplete:
    """Update a calendar's metadata. Requires Owner ("O") permission."""
    return obj_calendar_service.edit_calendar(calendar_id, edited_calendar, session)


@router.delete("/{calendar_id}")
def delete(calendar_id: str, session: SessionDep):
    """Permanently delete a calendar. Requires Owner ("O") permission."""
    return obj_calendar_service.delete_calendar(calendar_id, session)
