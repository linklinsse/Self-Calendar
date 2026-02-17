from contextvars import ContextVar
from typing import Optional

from app.models.obj_user_model import ObjUserModel


_loged_user: ContextVar[Optional[ObjUserModel]] = ContextVar(
    "loged_user", default=None
)


def get_loged_user_context() -> ObjUserModel | None:
    return _loged_user.get()


def set_loged_user_context(user: ObjUserModel | None):
    _loged_user.set(user)
