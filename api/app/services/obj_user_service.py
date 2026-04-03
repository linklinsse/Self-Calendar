from sqlmodel import exists, select

from fastapi import HTTPException

from app.common.db_connection import SessionDep
from app.common.contexts.loged_user_context import get_loged_user_context
from app.common.decorators.db_session_injector import db_session_injector
from app.common.errors import raise_app_error, AppErrorCode
from app.models.obj_user_model import ObjUserModel
from app.schemas.obj_user_schema import ObjUserSchemaChangePassword, ObjUserSchemaCreate
from app.common.security import hash_password, verify_password
from app.common.config import settings


@db_session_injector
def get_user(user_id: str, db_session: SessionDep) -> ObjUserModel:
    """Fetch a user by primary key.

    Args:
        user_id: The UUID of the user to retrieve.

    Returns:
        The matching ObjUserModel instance.

    Raises:
        HTTPException 404 if no user exists with the given ID.
    """
    db_user = db_session.get(ObjUserModel, user_id)
    if not db_user:
        raise_app_error(AppErrorCode.USER_NOT_FOUND)
    return db_user

@db_session_injector
def find_user_by_username(username: str, db_session: SessionDep) -> ObjUserModel:
    db_user = db_session.exec(
        select(ObjUserModel).where(
            ObjUserModel.username == username
        )
    ).first()
    return db_user

@db_session_injector
def create_user(new_user: ObjUserSchemaCreate, db_session: SessionDep) -> ObjUserModel:
    if not settings.USER_CREATION:
        return raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    new_user_model = {
        username: new_user.username,
        hashed_password: hash_password(new_user.password)
    }

    db_session.add(new_user_model)
    db_session.commit()
    db_session.refresh(new_user_model)

    return new_user_model

@db_session_injector
def update_user_password(password_data: ObjUserSchemaChangePassword, db_session: SessionDep) -> ObjUserModel:
    loged_user = get_loged_user_context()
    if not loged_user:
        return raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    if loged_user.id != password_data.user_id:
        return raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    if not verify_password(password_data.old_password, loged_user.hashed_password):
        return raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    loged_user.hashed_password = hash_password(password_data.new_password)

    db_session.add(loged_user)
    db_session.commit()
    db_session.refresh(loged_user)

    return loged_user
