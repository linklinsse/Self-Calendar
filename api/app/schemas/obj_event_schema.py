from pydantic import BaseModel, Field

from app.schemas.common_fields import CommonFieldDescription, CommonFieldTitle
from app.schemas.obj_event_recurence_schema import ObjEventRecurenceSchemaComplete, ObjEventRecurenceSchemaEdit, ObjEventRecurenceSchemaCreate


class ObjEventSchemaComplete(BaseModel):
    id: str
    calendar_id: str
    title: CommonFieldTitle
    description: CommonFieldDescription
    date_start: int
    date_end: int
    category_id: str | None = Field(default=None)
    color: str | None = Field(default=None)
    address: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    recurence_id: str | None = Field(default=None)
    obj_recurence: ObjEventRecurenceSchemaComplete | None = Field(default=None)


class ObjEventSchemaCreate(BaseModel):
    """Client-supplied payload for creating an event.

    `recurence_id` is deliberately NOT a field here: it is server-owned and
    derived from `obj_recurence`. Accepting it from the client let any
    authenticated user bind their own event to a recurrence row belonging to
    a calendar they have no access to — reading its rule via GET, and
    destroying it (plus every exception on it) by deleting their own event,
    since delete_event cascades into the attached recurrence.
    """

    calendar_id: str
    title: CommonFieldTitle
    description: CommonFieldDescription
    date_start: int
    date_end: int
    category_id: str | None = Field(default=None)
    # Null = inherit the category's colour. See ObjEventModel.color.
    color: str | None = Field(default=None, max_length=7)
    address: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    obj_recurence: ObjEventRecurenceSchemaCreate | None = Field(default=None)


class ObjEventSchemaEdit(BaseModel):
    """All fields are optional — only provided fields are updated (PATCH semantics).

    As with ObjEventSchemaCreate, `recurence_id` is server-owned and absent
    on purpose — see that schema's docstring.
    """
    title: CommonFieldTitle | None = Field(default=None)
    description: CommonFieldDescription
    date_start: int | None = Field(default=None)
    date_end: int | None = Field(default=None)
    category_id: str | None = Field(default=None)
    color: str | None = Field(default=None, max_length=7)
    address: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    obj_recurence: ObjEventRecurenceSchemaCreate | ObjEventRecurenceSchemaEdit | None = Field(default=None)


class ObjEventOccurrenceSchema(BaseModel):
    """One materialised occurrence of an event.

    Returned by GET /event/range?expand=true. Carries the full event, plus
    the start/end of this particular occurrence — so a recurring event
    appears once per occurrence, with exclusions already removed and the
    recurrence rule already applied by the server.

    This exists so clients don't each have to reimplement recurrence
    expansion. The Android widget consumes it and expands nothing itself.
    """

    event: ObjEventSchemaComplete
    date_start: int
    date_end: int
