import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import settings
from app.common.db_connection import create_db_and_tables
from app.common.dependencies.verify_logged_user_dependency import verify_logged_user_dependency
from app.common.middleware.rate_limit_middleware import RateLimitMiddleware
from app.routing import (
    auth_routing,
    calendar_routing,
    category_routing,
    event_routing,
    user_calendar_routing,
    user_routing,
)


# ---------------------------------------------------------------------------
# Lifespan — runs once on startup and once on shutdown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: validate config, create DB tables, warn about CORS origins."""
    _require_real_secret_key()
    _require_persistent_db()
    create_db_and_tables()
    _warn_cors_origins()
    yield
    # Add shutdown logic here if needed (e.g. close connection pools)


def _require_real_secret_key() -> None:
    """Refuse to start with a placeholder SECRET_KEY.

    Both the built-in default ("change-me") and the placeholder shipped in
    every .env template ("change-me-use-openssl-rand-hex-32") start with
    "change-me" — treat either as unset. Every previously-issued JWT is
    forgeable by anyone who reads the source, so this must not be a silent
    fallback.
    """
    if settings.SECRET_KEY.startswith("change-me"):
        raise RuntimeError(
            "SECRET_KEY is still set to a placeholder value. Generate a "
            "real secret (e.g. `openssl rand -hex 32`) and set it in "
            "conf/.env before starting the API."
        )


# Set in api/Dockerfile. Its only job is to let the check below know it is
# running in a container, where an unmounted database path silently
# evaporates on every `docker compose down`. Outside a container the same
# path is just a file on disk and survives, so the check does not apply.
_IN_CONTAINER_ENV_VAR = "SELFCALENDAR_IN_CONTAINER"

# Where docker-compose.yml bind-mounts the host's ./db directory.
_CONTAINER_DB_MOUNT = "/work/db"


def _require_persistent_db() -> None:
    """In a container, refuse to start if the SQLite file is not on the mount.

    This is the single most-reported failure in this project: the database
    appears to reset on every `docker compose down && up`, and the account
    created a moment ago is gone.

    It is never a Docker or SQLite persistence bug. DB_URL defaults to
    `sqlite:///./dev.db`, which resolves to `/work/dev.db` — inside the
    container's own writable layer, *not* the bind-mounted `/work/db`. The
    container is destroyed on `down`, and the database with it. Anything
    that leaves DB_URL unset gets this: a missing `conf/.env` line, or
    copying `api/conf/.env.template` (which ships that dev default, correct
    when running outside Docker) instead of the root one.

    Until now that was entirely silent — the API started normally and served
    an empty database, so the symptom only showed up as lost data later. A
    startup failure with the actual reason is worth far more than a clean
    start on a database about to be discarded.
    """
    if not os.environ.get(_IN_CONTAINER_ENV_VAR):
        return

    url = settings.DB_URL
    if not url.startswith("sqlite"):
        return  # a real database server persists on its own terms

    # sqlite:///relative/path or sqlite:////absolute/path
    path = url.split("sqlite:///", 1)[-1]
    resolved = Path(path).resolve() if path else None

    if resolved and resolved.is_relative_to(_CONTAINER_DB_MOUNT):
        return

    raise RuntimeError(
        f"DB_URL resolves to {resolved}, which is inside the container and "
        f"will be destroyed on the next `docker compose down` — taking every "
        f"account and event with it.\n\n"
        f"Set DB_URL in conf/.env to a path under {_CONTAINER_DB_MOUNT}, "
        f"which is where docker-compose.yml mounts the host's ./db "
        f"directory:\n\n"
        f"    DB_URL=sqlite:///./db/prod.db\n\n"
        f"If conf/.env is missing entirely, copy the one at the repository "
        f"root: `cp conf/.env.template conf/.env` (note the root template, "
        f"not api/conf/.env.template — that one targets local development "
        f"outside Docker)."
    )


def _warn_cors_origins() -> None:
    """Print a visible warning for every CORS origin that has been allowed.

    An empty CORS_ORIGINS list (the default) means no cross-origin requests
    are permitted and no warning is printed. Any configured origin is printed
    to stderr so operators are aware of the exposure surface.
    """
    if not settings.CORS_ORIGINS:
        return

    print(
        "\n\033[33m[WARNING] CORS is enabled for the following origins:\033[0m",
        file=sys.stderr,
    )
    for origin in settings.CORS_ORIGINS:
        print(f"  \033[33m⚠  {origin}\033[0m", file=sys.stderr)
    print(
        "\033[33m  Ensure these origins are intentional before deploying.\033[0m\n",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Self Calendar API",
    version="0.0.1",
    lifespan=lifespan,
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
# Applied before CORS so blocked IPs never reach route handlers.
# Protected routes are declared in rate_limit_middleware.PROTECTED_ROUTES.
app.add_middleware(RateLimitMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Empty by default — configure CORS_ORIGINS in .env to allow specific origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Protected routers — every route below requires a valid Bearer token.
#
# verify_logged_user_dependency decodes the token, fetches the user from DB,
# and populates the request-scoped context so services can call
# get_logged_user_context() without receiving the user as a parameter.
# ---------------------------------------------------------------------------
_auth_dep = [Depends(verify_logged_user_dependency)]

app.include_router(calendar_routing.router,      dependencies=_auth_dep)
app.include_router(user_calendar_routing.router, dependencies=_auth_dep)
app.include_router(user_routing.router,          dependencies=_auth_dep)
app.include_router(event_routing.router,         dependencies=_auth_dep)
app.include_router(category_routing.router,      dependencies=_auth_dep)

# Public router — no authentication required
app.include_router(auth_routing.router)
