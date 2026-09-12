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


class CalendarReorderSchema(BaseModel):
    """Body of PATCH /calendar/reorder.

    The full, desired order of the caller's own calendars, listed by id.
    Must contain exactly the calendars the caller already belongs to, each
    once — see reorder_calendars in lnk_user_calendar_service.py.
    """

    calendar_ids: list[str]
