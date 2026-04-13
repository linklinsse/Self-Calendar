from sqlmodel import Session

from app.schemas.auth_schema import AuthSchema
from app.common.security import verify_password, encode_token
from app.services.obj_user_service import find_user_by_username
from app.common.errors import raise_app_error, AppErrorCode


def login(credentials: AuthSchema, session: Session) -> str:
    """Authenticate a user and return a signed JWT access token.

    Raises HTTP 401 (INVALID_CREDENTIALS) if the username does not exist
    or the password does not match.
    """
    user = find_user_by_username(credentials.username, session)

    if not user:
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    if not verify_password(credentials.password, user.hashed_password):
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    return encode_token(user)
