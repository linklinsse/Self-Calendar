from contextvars import ContextVar
from typing import Optional

from app.models.obj_user_model import ObjUserModel

# ---------------------------------------------------------------------------
# Request-scoped user context
#
# ContextVar ensures that each asyncio task (i.e. each HTTP request) has its
# own isolated copy of the variable. This avoids sharing state between
# concurrent requests, which would be a security risk.
# ---------------------------------------------------------------------------
_loged_user: ContextVar[Optional[ObjUserModel]] = ContextVar(
    "loged_user", default=None
)


def get_logged_user_context() -> ObjUserModel | None:
    """Return the authenticated user for the current request, or None."""
    return _loged_user.get()


def set_logged_user_context(user: ObjUserModel | None):
    """Store the authenticated user for the current request."""
    _loged_user.set(user)
