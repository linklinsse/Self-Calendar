from typing import List
from fastapi import APIRouter

from app.common.db_connection import SessionDep
from app.schemas.obj_event_schema import (
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)
from app.services import obj_event_service

router = APIRouter(prefix="/event", tags=["event"])


@router.post("/", response_model=ObjEventSchemaComplete)
async def create(
    new_event: ObjEventSchemaCreate, session: SessionDep
) -> ObjEventSchemaComplete:
    """Create a new event inside a calendar.

    Requires at least "W" (Write) permission on the target calendar.
    """
    return obj_event_service.create_event(new_event, session)


@router.get("/range/{calendar_id}", response_model=List[ObjEventSchemaComplete])
async def get_all(
    calendar_id: str,
    from_date: int,
    to_date: int,
    session: SessionDep,
    category_id: str | None = None,
) -> List[ObjEventSchemaComplete]:
    """Return events in a calendar that overlap a date range.

    Query params:
        from_date:   Range start as a Unix timestamp.
        to_date:     Range end as a Unix timestamp.
        category_id: Optional — filter results to a specific category.

    Requires at least "R" (read) permission.
    """
    return obj_event_service.get_all_event_between(
        calendar_id, from_date, to_date, category_id, session
    )


@router.get("/{event_id}", response_model=ObjEventSchemaComplete)
async def get(event_id: str, session: SessionDep) -> ObjEventSchemaComplete:
    """Return a single event by ID. Requires at least "R" (read) permission."""
    return obj_event_service.get_event(event_id, session)


@router.patch("/{event_id}", response_model=ObjEventSchemaComplete)
async def patch(
    event_id: str, edited_event: ObjEventSchemaEdit, session: SessionDep
) -> ObjEventSchemaComplete:
    """Partially update an event. Requires at least "W" (Write) permission."""
    return obj_event_service.edit_event(event_id, edited_event, session)


@router.delete("/{event_id}")
async def delete(event_id: str, session: SessionDep):
    """Delete an event. Requires at least "W" (Write) permission."""
    return obj_event_service.delete_event(event_id, session)
