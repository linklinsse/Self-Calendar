from pydantic import BaseModel

from app.common.enums import CalendarRight


class LnkUserCalendarSchemaComplete(BaseModel):
    id: str
    user_id: str
    calendar_id: str
    right: CalendarRight


class LnkUserCalendarSchemaCreate(BaseModel):
    username: str       # resolved to user_id in the service layer
    calendar_id: str
    right: CalendarRight


class LnkUserCalendarSchemaEdit(BaseModel):
    right: CalendarRight
