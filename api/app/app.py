import sys
from contextlib import asynccontextmanager

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
    """Startup: create DB tables, validate config, warn about CORS origins."""
    create_db_and_tables()
    _warn_cors_origins()
    yield
    # Add shutdown logic here if needed (e.g. close connection pools)


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
