from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.decorators.db_session_injector import db_session_injector
from app.common.dependencies.verify_loged_user_dependency import (
    verify_loged_user_dependency,
)
from app.models.obj_user_model import ObjUserModel
from app.routing import calendar_routing
from app.routing import user_calendar_routing
from app.routing import auth_routing
from app.routing import user_routing
from app.routing import event_routing
from app.routing import category_routing
from app.common.db_connection import SessionDep, create_db_and_tables
from app.schemas.obj_user_schema import ObjUserSchemaComplete

# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(title="Self Calendar Api", version="0.0.1", dependencies=[])
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------------------------
# Protected routers
# Every route included here requires:
#   1. verify_loged_user_dependency  — rejects requests without a valid token
#   2. fill_loged_user_context_dependency — populates the request-scoped
#      user context so downstream code can call get_loged_user_context()
# ---------------------------------------------------------------------------
app.include_router(
    calendar_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
    ],
)
app.include_router(
    user_calendar_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
    ],
)
app.include_router(
    user_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
    ],
)
app.include_router(
    event_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
    ],
)
app.include_router(
    category_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
    ],
)

# Public router — no authentication required
app.include_router(auth_routing.router)

# Create all SQLModel tables on startup if they do not already exist
create_db_and_tables()


# ---------------------------------------------------------------------------
# Debug helper — kept for local development, NOT called in production
# ---------------------------------------------------------------------------
@db_session_injector
def create_user(db_session: SessionDep):
    """Insert a hard-coded test user into the database."""
    user = ObjUserSchemaComplete(
        id="test", login="test", hashed_password="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    )
    db_calendar = ObjUserModel.model_validate(user)
    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)


# Uncomment the line below to seed the test user on first run:
# create_user()
