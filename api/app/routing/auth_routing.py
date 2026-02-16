from fastapi import APIRouter

from app.services import auth_service


router = APIRouter(prefix="/auth")


# TODO ofc
@router.get("/login")
async def login():
    return auth_service.login()
