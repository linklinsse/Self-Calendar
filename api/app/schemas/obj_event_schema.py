from pydantic import BaseModel, Field

from app.schemas.common_fields import CommonFieldTitle


class ObjEventSchema(BaseModel):
    id: str | None = Field(default=None)
    calendar_id: str
    title: CommonFieldTitle
    description: str | None = Field(default=None)
    date_start: int
    date_end: int
    category_id: str | None = Field(default=None)
    adresse: str | None = Field(default=None)
    reminder: str | None = Field(default=None)
    recurrence_id: str | None = Field(default=None)
