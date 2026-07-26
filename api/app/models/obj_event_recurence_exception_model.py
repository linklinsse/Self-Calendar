from uuid import uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.obj_event_recurence_model import ObjEventRecurenceModel

class ObjEventRecurenceExceptionModel(SQLModel, table=True):
    __tablename__ = "obj_event_recurrence_exception"

    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    recurrence_id: str = Field(foreign_key="obj_event_recurence.id", nullable=False, index=True)
    date: int = Field(nullable=False)  # unix timestamp of the skipped occurrence

    obj_recurence: ObjEventRecurenceModel = Relationship(back_populates="obj_exceptions")
