from typing import List
from fastapi import APIRouter, Query
from typing import Annotated
from sys import maxsize

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


@router.get("/range", response_model=List[ObjEventSchemaComplete])
async def get_all(
    session: SessionDep,
    calendar_ids: Annotated[list[str] | None, Query()] = [],
    from_date: int | None = 0,
    to_date: int | None = maxsize,
    category_ids: Annotated[list[str] | None, Query()] = None
) -> List[ObjEventSchemaComplete]:
    """Return events in a calendar that overlap a date range.

    Query params:
        calendar_ids:  Calendar list.
        from_date:     Optional — Range start as a Unix timestamp.
        to_date:       Optional — Range end as a Unix timestamp.
        category_ids:  Optional — filter results to a specific category.

    Requires at least "R" (read) permission.
    """

    return obj_event_service.get_all_event_between(
        calendar_ids, from_date, to_date, category_ids, session
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

@router.delete("/{event_id}/{date}")
async def add_exception_event_recurence(event_id: str, date: int, session: SessionDep):
    """Delete an event recurence. Requires at least "W" (Write) permission."""
    return obj_event_service.add_exception_event_recurence(event_id, date, session)
