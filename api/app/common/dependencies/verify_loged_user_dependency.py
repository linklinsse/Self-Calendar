from typing import Annotated

from fastapi import HTTPException, Depends
import app.common.security as security


async def verify_loged_user_dependency(
    token: Annotated[str, Depends(security.oauth2_scheme)],
):
    """FastAPI dependency — gate access to protected routes.

    Raises HTTP 401 if no token is present.
    This dependency runs before fill_loged_user_context_dependency and acts
    as the first line of authentication enforcement.

    TODO: Validate the token signature/expiry here once real JWTs are in use.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return token
