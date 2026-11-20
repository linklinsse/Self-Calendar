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

from typing import Literal

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
    # Tokens are signed and verified with the shared SECRET_KEY, so only the
    # HMAC family makes sense. A free-form string let a typo or an
    # asymmetric/"none" algorithm through to PyJWT at runtime; restricting
    # it here turns that into a clear error at startup instead.
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # 30 days. Long-lived on purpose: it exists so the Android home-screen
    # widget can keep working without the user opening the app, which they
    # may not do for weeks. Safe to keep this long because it carries
    # tokenVersion — a password change invalidates it immediately — and
    # because its "type" claim means it cannot be used as an access token.
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200

    # ── Database ────────────────────────────────
    DB_URL: str = "sqlite:///./dev.db"

    # ── CORS ────────────────────────────────────
    # Empty by default — no cross-origin requests are allowed unless explicitly
    # configured. Add origins in .env as a comma-separated list:
    #   CORS_ORIGINS=http://localhost:5173,https://app.example.com
    # A warning is printed at startup for every origin that is allowed.
    CORS_ORIGINS: list[str] = []

    # ── Rate limiting ────────────────────────────
    # Number of failed requests from an IP, within RATE_LIMIT_WINDOW_SECONDS,
    # before it is blocked.
    RATE_LIMIT_MAX_FAILURES: int = 5
    # How far back (seconds) failures are counted. A success does not clear
    # them — see rate_limit_middleware.py for why.
    RATE_LIMIT_WINDOW_SECONDS: int = 900
    # How long (seconds) a blocked IP must wait before trying again.
    RATE_LIMIT_TIMEOUT_SECONDS: int = 180


# Single shared instance – import this, don't re-instantiate.
settings = Settings()
