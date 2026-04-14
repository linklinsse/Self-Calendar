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
    # Empty by default — no cross-origin requests are allowed unless explicitly
    # configured. Add origins in .env as a comma-separated list:
    #   CORS_ORIGINS=http://localhost:5173,https://app.example.com
    # A warning is printed at startup for every origin that is allowed.
    CORS_ORIGINS: list[str] = []

    # ── Rate limiting ────────────────────────────
    # Number of consecutive failed requests from an IP before it is blocked.
    RATE_LIMIT_MAX_FAILURES: int = 5
    # How long (seconds) a blocked IP must wait before trying again.
    RATE_LIMIT_TIMEOUT_SECONDS: int = 180


# Single shared instance – import this, don't re-instantiate.
settings = Settings()
