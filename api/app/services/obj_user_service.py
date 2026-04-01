from sqlmodel import exists, select

from fastapi import HTTPException
from app.common.db_connection import SessionDep
from app.common.decorators.db_session_injector import db_session_injector
from app.models.obj_user_model import ObjUserModel
from app.common.errors import raise_app_error, AppErrorCode


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
