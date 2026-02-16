from contextvars import ContextVar
from typing import Optional

from app.schemas.obj_user_schema import ObjUserSchemaComplete


_loged_user: ContextVar[Optional[ObjUserSchemaComplete]] = ContextVar(
    "loged_user", default=None
)


def get_loged_user_context() -> ObjUserSchemaComplete | None:
    return _loged_user.get()


def set_loged_user_context(user: ObjUserSchemaComplete | None):
    _loged_user.set(user)
