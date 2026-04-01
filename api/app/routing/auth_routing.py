from fastapi import APIRouter

from app.services import auth_service
from app.schemas.auth_schema import AuthSchema

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(
    response_model: AuthSchema
):
    """Authenticate a user and return an access token."""
    return auth_service.login(response_model)
