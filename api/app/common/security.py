from fastapi.security import OAuth2PasswordBearer

from app.schemas.obj_user_schema import ObjUserSchemaComplete
from app.services.obj_user_service import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    return password


def encode_token(user: ObjUserSchemaComplete) -> str:
    return user.id


def decode_token(token) -> str:
    return token


def get_current_user(token: str) -> ObjUserSchemaComplete:
    decoded_token = decode_token(token)
    user = get_user(decoded_token)
    return user
