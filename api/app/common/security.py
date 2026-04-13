"""
app/common/security.py
-----------------------
Authentication utilities:
  - OAuth2 bearer scheme declaration
  - JWT token creation and verification
  - Password hashing / verification

All secrets come from `settings` (i.e. the .env file).
"""

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

from app.schemas.obj_user_schema import ObjUserSchemaComplete
from app.common.config import settings
from app.common.errors import AppErrorCode, raise_app_error

# ── OAuth2 scheme ─────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ── Password hashing ──────────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True when *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)

# ── JWT ───────────────────────────────────────────────────────────────────────

def encode_token(user: ObjUserSchemaComplete) -> str:
    """Create a signed JWT.

    A `exp` claim is added automatically using
    `settings.ACCESS_TOKEN_EXPIRE_MINUTES`.
    """

    payload = {}
    payload["userId"] = user.id
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["exp"] = expire
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> str:
    """Decode and verify a JWT.

    Raises `HTTP 401` (INVALID_TOKEN) on any failure.
    """
    try:
        payload: dict[str, object] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload["userId"]
    except JWTError:
        raise_app_error(AppErrorCode.INVALID_TOKEN)
        raise  # unreachable – satisfies type-checker


def get_current_user(token: str, session) -> ObjUserSchemaComplete:
    """Resolve a raw token string to the corresponding user object."""
    from app.services.obj_user_service import get_user

    user_id = decode_token(token)
    return get_user(user_id, session)
