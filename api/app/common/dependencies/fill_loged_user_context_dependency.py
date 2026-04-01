from typing import Annotated
from fastapi import Depends

from app.common import security
from app.common.contexts.loged_user_context import set_loged_user_context
from app.services.obj_user_service import get_user


async def fill_loged_user_context_dependency(
    token: Annotated[str, Depends(security.oauth2_scheme)],
):
    """FastAPI dependency — populate the request-scoped user context.

    Decodes the Bearer token and stores the matching user object so that
    service-layer code can retrieve it via get_loged_user_context() without
    needing the token to be passed explicitly through every function call.

    The sentinel value "undefined" is treated as an absent token so that
    unauthenticated paths that still run this dependency don't crash.
    """
    if token != "undefined":
        # Decode the token to get the user ID, then fetch the user from DB
        set_loged_user_context(get_user(token))
    else:
        set_loged_user_context(None)
    return token
