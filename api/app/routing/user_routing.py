from fastapi import APIRouter

from app.common.contexts.loged_user_context import get_loged_user_context
from app.schemas.obj_user_schema import ObjUserSchemaComplete, ObjUserSchemaChangePassword, ObjUserSchemaCreate
from app.services import obj_user_service

router = APIRouter(prefix="/user")

@router.get("/me", response_model=ObjUserSchemaComplete)
async def get() -> ObjUserSchemaComplete:
    """Return the profile of the currently authenticated user.

    The user object is read from the request-scoped context, which is
    populated by fill_loged_user_context_dependency before this handler runs.
    """
    return get_loged_user_context()

@router.post("/", response_model=ObjUserSchemaComplete)
async def get(new_user: ObjUserSchemaCreate) -> ObjUserSchemaComplete:
    return obj_user_service.create_user(new_user)

@router.patch("/", response_model=ObjUserSchemaComplete)
async def get(password_data: ObjUserSchemaChangePassword) -> ObjUserSchemaComplete:
    return obj_user_service.update_user_password(password_data)
