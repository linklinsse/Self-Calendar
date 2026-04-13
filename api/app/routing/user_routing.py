from fastapi import APIRouter

from app.schemas.obj_user_schema import ObjUserSchemaComplete, ObjUserSchemaChangePassword, ObjUserSchemaCreate
from app.services import obj_user_service

router = APIRouter(prefix="/user", tags=["user"])

@router.patch("/", response_model=ObjUserSchemaComplete)
async def edit(password_data: ObjUserSchemaChangePassword) -> ObjUserSchemaComplete:
    return obj_user_service.update_user_password(password_data)
