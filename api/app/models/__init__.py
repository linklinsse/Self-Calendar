"""
Model package.

Re-exports every table model so that importing `app.models` registers all of
them on `SQLModel.metadata`.

This matters for Alembic: autogenerate compares the metadata against the live
database, and a model that has not been imported simply is not in the
metadata. With an empty __init__ the comparison sees no tables at all and
generates a migration that drops the entire schema — silently, and it looks
plausible until you run it.
"""

from app.models.lnk_user_calendar_model import LnkUserCalendarModel
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_category_model import ObjCategoryModel
from app.models.obj_event_model import ObjEventModel
from app.models.obj_event_recurence_exception_model import (
    ObjEventRecurenceExceptionModel,
)
from app.models.obj_event_recurence_model import ObjEventRecurenceModel
from app.models.obj_user_model import ObjUserModel

__all__ = [
    "LnkUserCalendarModel",
    "ObjCalendarModel",
    "ObjCategoryModel",
    "ObjEventModel",
    "ObjEventRecurenceExceptionModel",
    "ObjEventRecurenceModel",
    "ObjUserModel",
]
