from typing import Annotated
from fastapi import Depends

from app.common import security
from app.common.contexts.loged_user_context import set_loged_user_context
from app.services.obj_user_service import get_user


async def fill_loged_user_context_dependency(
    token: Annotated[str, Depends(security.oauth2_scheme)],
):
    if token != "undefined":
        set_loged_user_context(get_user(token))
    else:
        set_loged_user_context(None)
    return token
