from fastapi import APIRouter

from app.services import auth_service
from app.schemas.auth_schema import AuthSchema
from app.common.contexts.loged_user_context import get_loged_user_context
from app.schemas.obj_user_schema import ObjUserSchemaComplete

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(
    response_model: AuthSchema
):
    """Authenticate a user and return an access token."""
    return auth_service.login(response_model)

@router.get("/me", response_model=ObjUserSchemaComplete)
async def get() -> ObjUserSchemaComplete:
    """Return the profile of the currently authenticated user.

    The user object is read from the request-scoped context, which is
    populated by fill_loged_user_context_dependency before this handler runs.
    """
    return get_loged_user_context()