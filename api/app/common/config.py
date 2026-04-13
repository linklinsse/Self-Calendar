"""
app/common/config.py
--------------------
Application settings loaded from the .env file.

All environment variables are declared here as typed fields.
Import `settings` anywhere in the app instead of reading os.environ directly.

Usage:
    from app.common.config import settings

    engine = create_engine(settings.DB_URL)
    token = jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./conf/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── General ───────────────────────────────────
    USER_CREATION: bool = True

    # ── Authentication ──────────────────────────
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── Database ────────────────────────────────
    DB_URL: str = "sqlite:///./dev.db"

    # ── CORS ────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Example in .env:  CORS_ORIGINS=http://localhost:5173,http://localhost:8080
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5173",
    ]


# Single shared instance – import this, don't re-instantiate.
settings = Settings()
