from pydantic import BaseModel


class LnkUserCalendarSchemaComplete(BaseModel):
    id: str
    user_id: str
    calendar_id: str
    right: str  # TODO Enum


class LnkUserCalendarSchemaCreate(BaseModel):
    user_id: str
    calendar_id: str
    right: str  # TODO Enum


class LnkUserCalendarSchemaEdit(BaseModel):
    right: str  # TODO Enum
