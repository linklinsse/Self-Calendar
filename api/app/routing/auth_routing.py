from fastapi import APIRouter, Depends

from app.common.db_connection import SessionDep
from app.common.dependencies.verify_logged_user_dependency import verify_logged_user_dependency
from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.config import settings
from app.schemas.auth_schema import (
    AuthConfigSchema,
    AuthSchema,
    RefreshRequestSchema,
    RefreshTokenSchema,
)
from app.schemas.obj_user_schema import ObjUserSchemaComplete, ObjUserSchemaCreate
from app.services import auth_service, obj_user_service

router = APIRouter(prefix="/auth", tags=["auths"])


@router.get("/config", response_model=AuthConfigSchema)
def get_config() -> AuthConfigSchema:
    """Public, unauthenticated: what the login screen needs to render itself.

    Only `user_creation` so far. Without it the client has no way to know
    whether registration is open, so it showed a Register tab on every
    deployment — including the ones the README tells operators to close.
    """
    return AuthConfigSchema(user_creation=settings.USER_CREATION)


@router.post("/refresh-token", response_model=RefreshTokenSchema)
def create_refresh_token(
    session: SessionDep,
    _: None = Depends(verify_logged_user_dependency),
) -> RefreshTokenSchema:
    """Mint a long-lived refresh token for the authenticated caller.

    Requested by the app so it can hand one to the Android home-screen
    widget, which otherwise stops working the moment its access token
    expires — the user may not open the app for weeks.
    """
    return RefreshTokenSchema(
        refresh_token=auth_service.issue_refresh_token(session)
    )


@router.post("/refresh")
def refresh(payload: RefreshRequestSchema, session: SessionDep) -> str:
    """Exchange a refresh token for a fresh access token.

    Unauthenticated: the refresh token is itself the credential. Returns a
    bare token string, matching /auth/login's shape.
    """
    return auth_service.refresh_access_token(payload.refresh_token, session)


@router.post("/login")
def login(credentials: AuthSchema, session: SessionDep):
    """Authenticate a user and return a signed JWT access token."""
    return auth_service.login(credentials, session)


@router.post("/register", response_model=ObjUserSchemaComplete)
def register(new_user: ObjUserSchemaCreate, session: SessionDep) -> ObjUserSchemaComplete:
    """Create a new user account."""
    return obj_user_service.create_user(new_user, session)


@router.get(
    "/me",
    response_model=ObjUserSchemaComplete,
    dependencies=[Depends(verify_logged_user_dependency)],
)
def get_me() -> ObjUserSchemaComplete:
    """Return the profile of the currently authenticated user."""
    return get_logged_user_context()
