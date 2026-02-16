
from typing import Annotated

from fastapi import HTTPException, Header, Depends, Request
import app.common.security as security

from starlette.middleware.base import BaseHTTPMiddleware
from app.schemas.obj_user_schema import ObjUserSchemaComplete
from app.services.obj_user_service import get_user


async def verify_token(token: Annotated[str, Depends(security.oauth2_scheme)]):
    print(token)
    return token
