from fastapi import APIRouter

from app.common.contexts.loged_user_context import get_loged_user_context
from app.schemas.obj_user_schema import ObjUserSchemaComplete


router = APIRouter(prefix="/user")


@router.get("/me", response_model=ObjUserSchemaComplete)
async def get() -> ObjUserSchemaComplete:
    return get_loged_user_context()
