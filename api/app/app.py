from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import settings
from app.common.db_connection import create_db_and_tables
from app.common.dependencies.verify_loged_user_dependency import verify_loged_user_dependency
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
    """Create database tables on startup if they do not already exist."""
    create_db_and_tables()
    yield
    # Add any shutdown logic here (e.g. close connection pools)


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Self Calendar API",
    version="0.0.1",
    lifespan=lifespan,
)

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
# verify_loged_user_dependency decodes the token, fetches the user from DB,
# and populates the request-scoped context so services can call
# get_loged_user_context() without receiving the user as a parameter.
# ---------------------------------------------------------------------------
_auth_dep = [Depends(verify_loged_user_dependency)]

app.include_router(calendar_routing.router,      dependencies=_auth_dep)
app.include_router(user_calendar_routing.router, dependencies=_auth_dep)
app.include_router(user_routing.router,          dependencies=_auth_dep)
app.include_router(event_routing.router,         dependencies=_auth_dep)
app.include_router(category_routing.router,      dependencies=_auth_dep)

# Public router — no authentication required
app.include_router(auth_routing.router)
