from pydantic import BaseModel, Field
from typing import Annotated


class ObjEventRecurrenceSchema(BaseModel):
    id: str | None = Field(default=None)
    pattern_type: str  # TODO Enum
    end_date: int | None = Field(default=None)
    occurrence_count: int | None = Field(default=None)
    days_of_week: Annotated[
        str, Field(min_length=7, max_length=7, pattern="^[0-1]{7}$")
    ]
    interval: int | None = Field(default=None)
