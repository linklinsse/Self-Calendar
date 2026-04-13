from fastapi import Depends, APIRouter

from app.services import auth_service
from app.schemas.auth_schema import AuthSchema
from app.common.contexts.loged_user_context import get_loged_user_context
from app.schemas.obj_user_schema import ObjUserSchemaComplete, ObjUserSchemaCreate
from app.common.dependencies.verify_loged_user_dependency import (
    verify_loged_user_dependency,
)
from app.services import obj_user_service

router = APIRouter(prefix="/auth", tags=["login"])


@router.post("/login")
async def login(
    response_model: AuthSchema
):
    """Authenticate a user and return an access token."""
    return auth_service.login(response_model)

@router.post("/register", response_model=ObjUserSchemaComplete)
async def register(new_user: ObjUserSchemaCreate) -> ObjUserSchemaComplete:
    return obj_user_service.create_user(new_user)

@router.get(
    "/me",
    response_model=ObjUserSchemaComplete,
    dependencies=[
        Depends(verify_loged_user_dependency),
    ],
)
async def getAuth() -> ObjUserSchemaComplete:
    """Return the profile of the currently authenticated user.

    The user object is read from the request-scoped context, which is
    populated by fill_loged_user_context_dependency before this handler runs.
    """
    return get_loged_user_context()