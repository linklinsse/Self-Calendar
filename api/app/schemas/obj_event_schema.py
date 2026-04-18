from pydantic import BaseModel, Field

from app.schemas.common_fields import CommonFieldTitle
from app.schemas.obj_event_recurence_schema import ObjEventRecurenceSchemaComplete, ObjEventRecurenceSchemaEdit, ObjEventRecurenceSchemaCreate


class ObjEventSchemaComplete(BaseModel):
    id: str
    calendar_id: str
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    date_start: int
    date_end: int
    category_id: str | None = Field(default=None)
    address: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    recurence_id: str | None = Field(default=None)
    obj_recurence: ObjEventRecurenceSchemaComplete | None = Field(default=None)


class ObjEventSchemaCreate(BaseModel):
    calendar_id: str
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    date_start: int
    date_end: int
    category_id: str | None = Field(default=None)
    address: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    recurence_id: str | None = Field(default=None)
    obj_recurence: ObjEventRecurenceSchemaCreate | None = Field(default=None)


class ObjEventSchemaEdit(BaseModel):
    """All fields are optional — only provided fields are updated (PATCH semantics)."""
    title: CommonFieldTitle | None = Field(default=None)
    description: str | None = Field(default=None)
    date_start: int | None = Field(default=None)
    date_end: int | None = Field(default=None)
    category_id: str | None = Field(default=None)
    address: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    recurence_id: str | None = Field(default=None)
    obj_recurence: ObjEventRecurenceSchemaCreate | ObjEventRecurenceSchemaEdit | None = Field(default=None)
