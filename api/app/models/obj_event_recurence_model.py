from uuid import uuid4
from typing import TYPE_CHECKING, List
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # Only needed for static analysis — SQLModel resolves these forward
    # refs at runtime via its own registry, not via this module's imports.
    from app.models.obj_event_model import ObjEventModel
    from app.models.obj_event_recurence_exception_model import (
        ObjEventRecurenceExceptionModel,
    )

class ObjEventRecurenceModel(SQLModel, table=True):
    """Database model for a calendar event recurence."""

    __tablename__ = "obj_event_recurence"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()), index=True)
    type: str = Field(nullable=False, min_length=1, max_length=1, default='D')
    interval: int = Field(nullable=False)
    days: str | None  = Field(nullable=True, min_length=7, max_length=7)
    endType: str = Field(nullable=False, min_length=1, max_length=1, default='N')
    count: int | None  = Field(nullable=True)
    until: int | None  = Field(nullable=True)
    estimated_end_date: int | None = Field(nullable=True)

    obj_event: List["ObjEventModel"] = Relationship(
        back_populates="obj_recurence"
    )
    obj_exceptions: List["ObjEventRecurenceExceptionModel"] = Relationship(
        back_populates="obj_recurence"
    )