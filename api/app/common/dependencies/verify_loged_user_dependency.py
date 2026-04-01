from typing import Annotated

from fastapi import HTTPException, Depends
from app.common.errors import AppErrorCode, raise_app_error
from app.common.security import get_current_user, oauth2_scheme
from app.common.contexts.loged_user_context import set_loged_user_context


async def verify_loged_user_dependency(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    """Decode *token*, fetch the user and populate the context."""
    if token:
        # Decode the token to get the user ID, then fetch the user from DB
        user = get_current_user(token)
        if user:
            set_loged_user_context(user)
            return True

    raise_app_error(AppErrorCode.INVALID_TOKEN)

