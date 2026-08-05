from pydantic import BaseModel


class AuthSchema(BaseModel):
    username: str
    password: str

class AuthConfigSchema(BaseModel):
    """Public server capabilities, served by GET /auth/config."""

    user_creation: bool


class RefreshRequestSchema(BaseModel):
    """Body of POST /auth/refresh."""

    refresh_token: str


class RefreshTokenSchema(BaseModel):
    """Response of POST /auth/refresh-token."""

    refresh_token: str
