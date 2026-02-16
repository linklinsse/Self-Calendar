from typing import Annotated

from fastapi import HTTPException, Depends
import app.common.security as security


async def verify_loged_user_dependency(
    token: Annotated[str, Depends(security.oauth2_scheme)],
):
    if not token:
        raise HTTPException(status_code=400, detail="Invalid token")
    return token
