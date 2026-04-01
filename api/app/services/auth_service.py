
from app.schemas.auth_schema import AuthSchema

from app.common.security import verify_password, encode_token, hash_password
from app.services.obj_user_service import find_user_by_username
from app.common.errors import raise_app_error, AppErrorCode

def login(response_model: AuthSchema):
    """Authenticate a user and return an access token."""
    user = find_user_by_username(response_model.username)

    if not user:
      raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    valid = verify_password(response_model.password, user.hashed_password)
    if not valid:
      raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    return encode_token(user)
