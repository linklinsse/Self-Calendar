from fastapi import APIRouter

from app.services import auth_service

router = APIRouter(prefix="/auth")


@router.get("/login")
async def login():
    """Authenticate a user and return an access token.

    TODO: Switch to POST, accept OAuth2PasswordRequestForm, and return a
    proper {"access_token": ..., "token_type": "bearer"} payload.
    """
    return auth_service.login()
