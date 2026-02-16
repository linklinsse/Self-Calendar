
from fastapi import APIRouter, Request

from app.common.decorators.current_user_injector import get_current_user
from app.schemas.obj_user_schema import ObjUserSchemaComplete


#TODO only loged user
router = APIRouter(prefix="/user")


@router.get("/me", response_model=ObjUserSchemaComplete)
async def get() -> ObjUserSchemaComplete:
    return get_current_user()