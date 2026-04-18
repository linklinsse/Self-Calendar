from pydantic import BaseModel, Field

from app.schemas.common_fields import CommonFieldTitle
from app.common.enums import EventRecurenceEndType, EventRecurenceType


class ObjEventRecurenceSchemaComplete(BaseModel):
    id: str
    type: EventRecurenceType
    interval: int
    days: str | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None)
    until: int | None = Field(default=None)


class ObjEventRecurenceSchemaCreate(BaseModel):
    type: EventRecurenceType
    interval: int
    days: str | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None)
    until: int | None = Field(default=None)


class ObjEventRecurenceSchemaEdit(BaseModel):
    id: str
    type: EventRecurenceType
    interval: int
    days: str | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None)
    until: int | None = Field(default=None)