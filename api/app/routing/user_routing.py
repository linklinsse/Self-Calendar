from fastapi import APIRouter

from app.common.db_connection import SessionDep
from app.schemas.obj_user_schema import ObjUserSchemaComplete, ObjUserSchemaChangePassword
from app.services import obj_user_service

router = APIRouter(prefix="/user", tags=["user"])


@router.patch("/password", response_model=ObjUserSchemaComplete)
async def change_password(
    password_data: ObjUserSchemaChangePassword, session: SessionDep
) -> ObjUserSchemaComplete:
    """Change the password of the currently authenticated user."""
    return obj_user_service.update_user_password(password_data, session)
