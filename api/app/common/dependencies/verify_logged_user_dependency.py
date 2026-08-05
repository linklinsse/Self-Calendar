from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from app.common.db_connection import SessionDep
from app.common.errors import AppErrorCode, raise_app_error
from app.common.security import get_current_user, bearer_scheme
from app.common.contexts.logged_user_context import set_logged_user_context


async def verify_logged_user_dependency(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: SessionDep,
) -> None:
    """Decode the Bearer token, fetch the user, and populate the request context.

    Raises HTTP 401 (INVALID_TOKEN) if the token is missing, invalid, or
    does not correspond to an existing user.

    The session injected here is the same one used for the rest of the
    request — no extra connection is opened.

    Must stay `async def`: FastAPI runs sync (`def`) callables in a
    threadpool via a copy of the current context, and mutations to a
    ContextVar made inside a copied context don't propagate back out.
    Since this dependency calls set_logged_user_context(), keeping it a
    coroutine on the event loop is what lets that write actually reach the
    request's real context — route handlers can safely be plain `def`
    (they only read the context, via a copy taken after this already ran).
    """
    if credentials:
        user = get_current_user(credentials.credentials, session)
        if user:
            set_logged_user_context(user)
            return

    raise_app_error(AppErrorCode.INVALID_TOKEN)
