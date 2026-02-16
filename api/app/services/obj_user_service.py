from fastapi import HTTPException
from app.common.db_connection import SessionDep
from app.common.decorators.db_session_injector import db_session_injector
from app.models.obj_user_model import ObjUserModel
from app.schemas.obj_user_schema import ObjUserSchemaComplete


@db_session_injector
def get_user(user_id: str, db_session: SessionDep) -> ObjUserSchemaComplete:
    db_user = db_session.get(ObjUserModel, {"id": user_id})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
