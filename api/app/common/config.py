
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

# TODO Remake wiht default value and generate file if not existant
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./conf/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── General ───────────────────────────────────
    USER_CREATION: str = True

    # ── Authentication ──────────────────────────
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── Database ────────────────────────────────
    DB_URL: str = "sqlite:///./dev.db"


# Single shared instance – import this, don't re-instantiate.
settings = Settings()
