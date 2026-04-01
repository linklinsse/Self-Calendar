from fastapi.security import OAuth2PasswordBearer

from app.schemas.obj_user_schema import ObjUserSchemaComplete
from app.services.obj_user_service import get_user

# FastAPI OAuth2 scheme — reads the Bearer token from the Authorization header.
# `tokenUrl` points to the login endpoint that issues the token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def hash_password(password: str) -> str:
    """Hash a plain-text password.

    TODO: Replace with a real hashing library such as bcrypt or argon2.
    """
    return password


def encode_token(user: ObjUserSchemaComplete) -> str:
    """Encode user data into a token string.

    TODO: Replace with a signed JWT (e.g. python-jose / PyJWT).
    Currently returns the user ID directly, which is insecure.
    """
    return user.id


def decode_token(token: str) -> str:
    """Decode a token and return the embedded user identifier.

    TODO: Replace with proper JWT verification.
    Currently returns the token as-is (mirrors encode_token stub above).
    """
    return token


def get_current_user(token: str) -> ObjUserSchemaComplete:
    """Resolve a raw token string to the corresponding user object."""
    decoded_token = decode_token(token)
    user = get_user(decoded_token)
    return user
