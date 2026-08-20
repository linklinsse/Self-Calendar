from sqlmodel import Session

from app.schemas.auth_schema import AuthSchema
from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    _DUMMY_HASH,
    encode_token,
    get_current_user,
    verify_password,
)
from app.services.obj_user_service import find_user_by_username
from app.common.errors import raise_app_error, AppErrorCode


def login(credentials: AuthSchema, session: Session) -> str:
    """Authenticate a user and return a signed JWT access token.

    Raises HTTP 401 (INVALID_CREDENTIALS) if the username does not exist,
    the password does not match, or the account is disabled.
    """
    user = find_user_by_username(credentials.username, session)

    if not user:
        # Verify against a dummy hash so this path takes about as long as
        # the username-exists path — otherwise usernames are enumerable
        # via response timing (a real bcrypt verify only happens below).
        verify_password(credentials.password, _DUMMY_HASH)
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    password_ok = verify_password(credentials.password, user.hashed_password)
    if not password_ok or user.disabled:
        raise_app_error(AppErrorCode.INVALID_CREDENTIALS)

    return encode_token(user)


def issue_refresh_token(session: Session) -> str:
    """Mint a long-lived refresh token for the already-authenticated caller.

    Deliberately a separate endpoint rather than something /auth/login hands
    out: login returns a bare token string, and widening that response would
    break every existing client. It also means a refresh token is only ever
    created when something actually needs one — currently just the Android
    widget, which has to keep working for weeks without the user opening the
    app.
    """
    db_user = get_logged_user_context()
    return encode_token(db_user, token_type=TOKEN_TYPE_REFRESH)


def refresh_access_token(refresh_token: str, session: Session) -> str:
    """Exchange a valid refresh token for a fresh access token.

    Unauthenticated by design — the refresh token *is* the credential. It is
    still checked for everything a normal token is: signature, expiry, the
    account not being disabled, and tokenVersion matching (so a password
    change kills outstanding refresh tokens too), plus its type claim, so an
    access token cannot be used here to mint an endless chain of new ones.

    No rotation: the same refresh token stays valid until it expires or the
    password changes. Rotation would need server-side state to detect reuse,
    which this project has no table for; without that, rotating would only
    add a way for a widget and an app racing each other to invalidate a
    perfectly good token.
    """
    db_user = get_current_user(refresh_token, session, expected_type=TOKEN_TYPE_REFRESH)
    return encode_token(db_user, token_type=TOKEN_TYPE_ACCESS)
