from pydantic import BaseModel, Field

from app.common.enums import CalendarRight
from app.schemas.common_fields import CommonFieldColor, CommonFieldDescription, CommonFieldTitle


class ObjCalendarSchemaComplete(BaseModel):
    id: str | None = Field(default=None)
    title: CommonFieldTitle
    description: CommonFieldDescription
    color: CommonFieldColor
    # The current user's permission level on this calendar ("R"/"W"/"O").
    # Populated in the service layer — see obj_calendar_service.py.
    user_right: CalendarRight | None = Field(default=None)


class ObjCalendarSchemaCreate(BaseModel):
    title: CommonFieldTitle
    description: CommonFieldDescription
    color: CommonFieldColor


class ObjCalendarSchemaEdit(BaseModel):
    """All fields are optional — only provided fields are updated (PATCH semantics)."""
    title: CommonFieldTitle | None = Field(default=None)
    description: CommonFieldDescription
    color: CommonFieldColor
