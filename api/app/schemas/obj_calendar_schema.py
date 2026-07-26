from pydantic import BaseModel, Field

from app.common.enums import CalendarRight
from app.schemas.common_fields import CommonFieldColor, CommonFieldTitle


class ObjCalendarSchemaComplete(BaseModel):
    id: str | None = Field(default=None)
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    color: CommonFieldColor
    # The current user's permission level on this calendar ("R"/"W"/"O").
    # Populated in the service layer — see obj_calendar_service.py.
    user_right: CalendarRight | None = Field(default=None)


class ObjCalendarSchemaCreate(BaseModel):
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    color: CommonFieldColor


class ObjCalendarSchemaEdit(BaseModel):
    """All fields are optional — only provided fields are updated (PATCH semantics)."""
    title: CommonFieldTitle | None = Field(default=None)
    description: str | None = Field(default=None)
    color: CommonFieldColor
