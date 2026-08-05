"""
app/common/security.py
-----------------------
Authentication utilities:
  - Bearer scheme declaration
  - JWT token creation and verification
  - Password hashing / verification

All secrets come from `settings` (i.e. the .env file).
"""

import jwt
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.schemas.obj_user_schema import ObjUserSchemaComplete
from app.common.config import settings
from app.common.errors import AppErrorCode, raise_app_error

# ── Bearer scheme ─────────────────────────────────────────────────────────────
# HTTPBearer, not OAuth2PasswordBearer: /auth/login takes a JSON body and
# returns a bare token string, not the OAuth2 password grant's form-encoded
# request + {access_token, token_type} response. OAuth2PasswordBearer
# advertised a flow this API doesn't implement, which is why the Swagger UI
# "Authorize" button never worked — HTTPBearer matches what's actually here
# (paste a token, sent as a plain `Authorization: Bearer <token>` header).

bearer_scheme = HTTPBearer(auto_error=False)

# ── Password hashing ──────────────────────────────────────────────────────────

# pwdlib wraps the `bcrypt` package directly (no passlib-style version
# sniffing / silent fallback to a removed stdlib module), and pinning the
# hasher to bcrypt explicitly keeps existing $2b$ hashes valid.
_pwd_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return _pwd_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True when *plain* matches *hashed*."""
    return _pwd_hash.verify(plain, hashed)


# A fixed dummy hash, verified on the "username not found" login path so a
# failed login takes roughly the same time whether the username exists or
# not — otherwise the bcrypt verify (~200-300ms) only running when the user
# exists makes usernames enumerable via response timing.
_DUMMY_HASH = hash_password("dummy-password-for-constant-time-comparison")

# ── JWT ───────────────────────────────────────────────────────────────────────

# Distinguishes the two kinds of token. Both are signed with the same secret,
# so without an explicit type claim a long-lived refresh token would be
# accepted anywhere an access token is — handing out a 90-day bearer
# credential for the whole API, which is exactly what refresh tokens exist to
# avoid. verify_logged_user_dependency rejects anything that is not "access";
# /auth/refresh rejects anything that is not "refresh".
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def encode_token(
    user: ObjUserSchemaComplete,
    token_type: str = TOKEN_TYPE_ACCESS,
) -> str:
    """Create a signed JWT.

    An `exp` claim is added automatically, using
    `settings.ACCESS_TOKEN_EXPIRE_MINUTES` for an access token and
    `settings.REFRESH_TOKEN_EXPIRE_MINUTES` for a refresh token.
    `tokenVersion` is embedded so that a password change (which bumps the
    user's token_version) invalidates every token issued before it — refresh
    tokens included, which is what makes them safe to keep this long.
    """

    minutes = (
        settings.REFRESH_TOKEN_EXPIRE_MINUTES
        if token_type == TOKEN_TYPE_REFRESH
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {}
    payload["userId"] = user.id
    payload["tokenVersion"] = user.token_version
    payload["type"] = token_type
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=minutes)
    payload["exp"] = expire
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> dict[str, object]:
    """Decode and verify a JWT, returning its payload.

    Raises `HTTP 401` (INVALID_TOKEN) on any failure, including a
    validly-signed token that is missing the `userId` claim.
    """
    try:
        payload: dict[str, object] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.PyJWTError:
        raise_app_error(AppErrorCode.INVALID_TOKEN)

    if "userId" not in payload:
        raise_app_error(AppErrorCode.INVALID_TOKEN)

    return payload


def get_current_user(
    token: str,
    session,
    expected_type: str = TOKEN_TYPE_ACCESS,
) -> ObjUserSchemaComplete:
    """Resolve a raw token string to the corresponding user object.

    Rejects tokens belonging to a disabled account, tokens issued before the
    user's last password change (see `token_version`), and tokens of the
    wrong kind.

    That last check is what keeps refresh tokens from being usable as access
    tokens: both are signed with the same secret, so without it a 30-day
    refresh token would authenticate every endpoint in the API — the exact
    thing short access-token lifetimes exist to prevent.

    Tokens minted before the `type` claim existed have no type at all. They
    are treated as access tokens, which is what they were, so an in-flight
    session survives the upgrade instead of everyone being logged out.
    """
    from app.services.obj_user_service import get_user

    payload = decode_token(token)

    token_type = payload.get("type", TOKEN_TYPE_ACCESS)
    if token_type != expected_type:
        raise_app_error(AppErrorCode.INVALID_TOKEN)

    user = get_user(payload["userId"], session)

    if user.disabled or payload.get("tokenVersion") != user.token_version:
        raise_app_error(AppErrorCode.INVALID_TOKEN)

    return user
