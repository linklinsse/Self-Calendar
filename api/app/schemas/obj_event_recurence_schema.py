from pydantic import BaseModel, Field, model_validator
from typing import Annotated

from app.schemas.obj_event_recurence_exception_schema import ObjEventRecurenceExceptionSchema
from app.common.enums import EventRecurenceEndType, EventRecurenceType


def _validate_end_type_fields(m: BaseModel) -> BaseModel:
    """Shared cross-field validation for Create/Edit recurrence schemas.

    Guards the failure modes in compute_estimated_end(): endType='C'
    requires a bounded count (unbounded count*interval can overflow
    datetime's internal timedelta), and endType='U' requires `until`.
    """
    if m.endType == EventRecurenceEndType.COUNT and m.count is None:
        raise ValueError("count is required when endType is 'C'")
    if m.endType == EventRecurenceEndType.UNTIL and m.until is None:
        raise ValueError("until is required when endType is 'U'")
    return m


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
    interval: int = Field(ge=1, le=1000)
    days: Annotated[
        str, Field(min_length=7, max_length=7, pattern="^[0-1]{7}$")
    ] | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None, ge=1, le=1000)
    until: int | None = Field(default=None)
    estimated_end_date: int | None = Field(default=None)
    obj_exceptions: list[ObjEventRecurenceExceptionSchema] = Field(default_factory=list)

    _validate_end_type = model_validator(mode="after")(_validate_end_type_fields)


class ObjEventRecurenceSchemaEdit(BaseModel):
    id: str
    type: EventRecurenceType
    interval: int = Field(ge=1, le=1000)
    days: Annotated[
        str, Field(min_length=7, max_length=7, pattern="^[0-1]{7}$")
    ] | None = Field(default=None)
    endType: EventRecurenceEndType
    count: int | None = Field(default=None, ge=1, le=1000)
    until: int | None = Field(default=None)
    estimated_end_date: int | None = Field(default=None)
    obj_exceptions: list[ObjEventRecurenceExceptionSchema] = Field(default_factory=list)

    _validate_end_type = model_validator(mode="after")(_validate_end_type_fields)
