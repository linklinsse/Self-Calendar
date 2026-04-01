from fastapi import HTTPException
from app.common.db_connection import SessionDep
from app.common.decorators.db_session_injector import db_session_injector
from app.models.obj_user_model import ObjUserModel


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
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
