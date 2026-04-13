from typing import Annotated

from fastapi import Depends
from app.common.db_connection import SessionDep
from app.common.errors import AppErrorCode, raise_app_error
from app.common.security import get_current_user, oauth2_scheme
from app.common.contexts.loged_user_context import set_loged_user_context


async def verify_loged_user_dependency(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> None:
    """Decode the Bearer token, fetch the user, and populate the request context.

    Raises HTTP 401 (INVALID_TOKEN) if the token is missing, invalid, or
    does not correspond to an existing user.

    The session injected here is the same one used for the rest of the
    request — no extra connection is opened.
    """
    if token:
        user = get_current_user(token, session)
        if user:
            set_loged_user_context(user)
            return

    raise_app_error(AppErrorCode.INVALID_TOKEN)
