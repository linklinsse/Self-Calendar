from typing import List
from fastapi import APIRouter

from app.schemas.obj_event_schema import (
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)
from app.services import obj_event_service

router = APIRouter(prefix="/event", tags=["event"])


@router.post("/", response_model=ObjEventSchemaComplete)
async def create(
    new_event: ObjEventSchemaCreate,
) -> ObjEventSchemaComplete:
    """Create a new event inside a calendar.

    Requires at least "W" (Edit) permission on the target calendar.
    """
    return obj_event_service.create_event(new_event)


@router.get("/range/{calendar_id}", response_model=List[ObjEventSchemaComplete])
async def get_all(
    calendar_id: str,
    from_date: int,
    to_date: int,
    category_id: str | None = None,
) -> List[ObjEventSchemaComplete]:
    """Return events in a calendar that overlap a date range.

    Query params:
        from_date:   Range start as a Unix timestamp (ms or s, must be consistent).
        to_date:     Range end as a Unix timestamp.
        category_id: Optional — filter results to a specific category.

    Requires at least "R" (read) permission.
    """
    return obj_event_service.get_all_event_between(
        calendar_id, from_date, to_date, category_id
    )


@router.get("/{event_id}", response_model=ObjEventSchemaComplete)
async def get(event_id: str) -> ObjEventSchemaComplete:
    """Return a single event by ID.

    Requires at least "R" (read) permission.
    """
    return obj_event_service.get_event(event_id)


@router.patch("/{event_id}", response_model=ObjEventSchemaComplete)
async def patch(
    event_id: str, edited_event: ObjEventSchemaEdit
) -> ObjEventSchemaComplete:
    """Partially update an event. Requires at least "W" (Edit) permission."""
    return obj_event_service.edit_event(event_id, edited_event)


@router.delete("/{event_id}")
async def delete(event_id: str):
    """Delete an event. Requires at least "W" (Edit) permission."""
    return obj_event_service.delete_event(event_id)
