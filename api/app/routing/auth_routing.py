from fastapi import APIRouter, Depends

from app.common.db_connection import SessionDep
from app.common.dependencies.verify_loged_user_dependency import verify_loged_user_dependency
from app.common.contexts.loged_user_context import get_loged_user_context
from app.schemas.auth_schema import AuthSchema
from app.schemas.obj_user_schema import ObjUserSchemaComplete, ObjUserSchemaCreate
from app.services import auth_service, obj_user_service

router = APIRouter(prefix="/auth", tags=[\"auth\"])


@router.post("/login")
async def login(credentials: AuthSchema, session: SessionDep):
    """Authenticate a user and return a signed JWT access token."""
    return auth_service.login(credentials, session)


@router.post("/register", response_model=ObjUserSchemaComplete)
async def register(new_user: ObjUserSchemaCreate, session: SessionDep) -> ObjUserSchemaComplete:
    """Create a new user account."""
    return obj_user_service.create_user(new_user, session)


@router.get(
    "/me",
    response_model=ObjUserSchemaComplete,
    dependencies=[Depends(verify_loged_user_dependency)],
)
async def get_me() -> ObjUserSchemaComplete:
    """Return the profile of the currently authenticated user."""
    return get_loged_user_context()
