from typing import List
from fastapi import APIRouter, Query
from typing import Annotated
from sys import maxsize

from app.common.db_connection import SessionDep
from app.common.utils.recurrence_expansion import expand_events
from app.schemas.obj_event_schema import (
    ObjEventOccurrenceSchema,
    ObjEventSchemaComplete,
    ObjEventSchemaCreate,
    ObjEventSchemaEdit,
)
from app.services import obj_event_service

router = APIRouter(prefix="/event", tags=["event"])


@router.post("/", response_model=ObjEventSchemaComplete)
def create(
    new_event: ObjEventSchemaCreate, session: SessionDep
) -> ObjEventSchemaComplete:
    """Create a new event inside a calendar.

    Requires at least "W" (Write) permission on the target calendar.
    """
    return obj_event_service.create_event(new_event, session)


@router.get("/range")
def get_all(
    session: SessionDep,
    calendar_ids: Annotated[list[str] | None, Query()] = [],
    from_date: int | None = 0,
    to_date: int | None = maxsize,
    category_ids: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 1000,
    expand: bool = False,
    timezone: str | None = None,
) -> List[ObjEventSchemaComplete] | List[ObjEventOccurrenceSchema]:
    """Return events in a calendar that overlap a date range.

    Query params:
        calendar_ids:  Calendar list.
        from_date:     Optional — Range start as a Unix timestamp.
        to_date:       Optional — Range end as a Unix timestamp.
        category_ids:  Optional — filter results to a specific category.
        limit:         Optional — max rows returned (default/max 1000). A
                        bare query with no from_date/to_date would otherwise
                        return every event ever created for the calendar.
        expand:        Optional — when true, recurring events are expanded
                        server-side into one entry per occurrence (exclusions
                        already applied) instead of being returned once with
                        their rule attached. Clients that set this do not
                        need to implement recurrence at all.
        timezone:      Optional — IANA name (e.g. "Europe/Paris") used to
                        resolve occurrences, since events are stored as bare
                        timestamps with no zone. Only meaningful with
                        expand=true. Defaults to UTC; a client should send
                        its own, or an event at 09:00 local will be expanded
                        against the wrong day boundaries.

    Requires at least "R" (read) permission.
    """

    events = obj_event_service.get_all_event_between(
        calendar_ids, from_date, to_date, category_ids, limit, session
    )

    if not expand:
        return events

    # The service returns ORM rows; validate each once into the response
    # schema and reuse it, rather than re-validating per occurrence — a
    # daily event over a month is 30 occurrences of the same event.
    by_id = {
        # from_attributes: these are SQLModel ORM rows, not dicts, and the
        # schema doesn't set it in its own config.
        event.id: ObjEventSchemaComplete.model_validate(
            event, from_attributes=True
        )
        for event in events
    }
    return [
        ObjEventOccurrenceSchema(
            event=by_id[occurrence["event_id"]],
            date_start=occurrence["date_start"],
            date_end=occurrence["date_end"],
        )
        for occurrence in expand_events(events, from_date, to_date, timezone)
    ]


@router.get("/{event_id}", response_model=ObjEventSchemaComplete)
def get(event_id: str, session: SessionDep) -> ObjEventSchemaComplete:
    """Return a single event by ID. Requires at least "R" (read) permission."""
    return obj_event_service.get_event(event_id, session)


@router.patch("/{event_id}", response_model=ObjEventSchemaComplete)
def patch(
    event_id: str, edited_event: ObjEventSchemaEdit, session: SessionDep
) -> ObjEventSchemaComplete:
    """Partially update an event. Requires at least "W" (Write) permission."""
    return obj_event_service.edit_event(event_id, edited_event, session)


@router.delete("/{event_id}")
def delete(event_id: str, session: SessionDep):
    """Delete an event. Requires at least "W" (Write) permission."""
    return obj_event_service.delete_event(event_id, session)

@router.delete("/{event_id}/{date}")
def add_exception_event_recurence(event_id: str, date: int, session: SessionDep):
    """Delete an event recurence. Requires at least "W" (Write) permission."""
    return obj_event_service.add_exception_event_recurence(event_id, date, session)
