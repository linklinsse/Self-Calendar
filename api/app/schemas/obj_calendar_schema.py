from pydantic import BaseModel, Field

from app.schemas.common_fields import CommonFieldColor, CommonFieldTitle


class ObjCalendarSchemaComplete(BaseModel):
    id: str | None = Field(default=None)
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    color: CommonFieldColor


class ObjCalendarSchemaCreate(BaseModel):
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    color: CommonFieldColor


class ObjCalendarSchemaEdit(BaseModel):
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    color: CommonFieldColor
