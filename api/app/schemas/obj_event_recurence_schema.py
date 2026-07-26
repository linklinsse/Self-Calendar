from pydantic import BaseModel, Field
from typing import Annotated

from app.schemas.obj_event_recurence_exception_schema import ObjEventRecurenceExceptionSchema
from app.common.enums import EventRecurenceEndType, EventRecurenceType


class ObjEventRecurenceSchemaComplete(BaseModel):
    id: str
    type: EventRecurenceType
    interval: int
    days: Annotated[
        str, Field(min_length=7, max_length=7, pattern="^[0-1]{7}$")
    ] | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None)
    until: int | None = Field(default=None)
    estimated_end_date: int | None = Field(default=None)
    obj_exceptions: list[ObjEventRecurenceExceptionSchema] = Field(default_factory=list)


class ObjEventRecurenceSchemaCreate(BaseModel):
    type: EventRecurenceType
    interval: int
    days: Annotated[
        str, Field(min_length=7, max_length=7, pattern="^[0-1]{7}$")
    ] | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None)
    until: int | None = Field(default=None)
    estimated_end_date: int | None = Field(default=None)
    obj_exceptions: list[ObjEventRecurenceExceptionSchema] = Field(default_factory=list)


class ObjEventRecurenceSchemaEdit(BaseModel):
    id: str
    type: EventRecurenceType
    interval: int
    days: Annotated[
        str, Field(min_length=7, max_length=7, pattern="^[0-1]{7}$")
    ] | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None)
    until: int | None = Field(default=None)
    estimated_end_date: int | None = Field(default=None)
    obj_exceptions: list[ObjEventRecurenceExceptionSchema] = Field(default_factory=list)