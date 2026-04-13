from sqlmodel import Session, select

from app.common.contexts.loged_user_context import get_loged_user_context
from app.common.errors import raise_app_error, AppErrorCode
from app.models.obj_user_model import ObjUserModel
from app.schemas.obj_user_schema import ObjUserSchemaChangePassword, ObjUserSchemaCreate
from app.common.security import hash_password, verify_password
from app.common.config import settings


def get_user(user_id: str, session: Session) -> ObjUserModel:
    """Fetch a user by primary key.

    Raises HTTP 404 (USER_NOT_FOUND) if no user exists with the given ID.
    """
    db_user = session.get(ObjUserModel, user_id)
    if not db_user:
        raise_app_error(AppErrorCode.USER_NOT_FOUND)
    return db_user


def find_user_by_username(username: str, session: Session) -> ObjUserModel | None:
    """Look up a user by their username. Returns None if not found."""
    return session.exec(
        select(ObjUserModel).where(ObjUserModel.username == username)
    ).first()


def create_user(new_user: ObjUserSchemaCreate, session: Session) -> ObjUserModel:
    """Register a new user account.

    Raises HTTP 401 if user creation is disabled via settings.
    """
    if not settings.USER_CREATION:
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    db_user = ObjUserModel(
        username=new_user.username,
        hashed_password=hash_password(new_user.password),
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


def update_user_password(
    password_data: ObjUserSchemaChangePassword, session: Session
) -> ObjUserModel:
    """Change the password of the currently authenticated user.

    The target user is always derived from the request-scoped context —
    clients cannot supply a user_id to act on behalf of another account.

    Raises HTTP 401 if the old password is incorrect or no user is in context.
    """
    logged_user = get_loged_user_context()
    if not logged_user:
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    if not verify_password(password_data.old_password, logged_user.hashed_password):
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    logged_user.hashed_password = hash_password(password_data.new_password)

    session.add(logged_user)
    session.commit()
    session.refresh(logged_user)

    return logged_user
