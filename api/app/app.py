from fastapi import Depends, FastAPI

from app.common.decorators.db_session_injector import db_session_injector
from app.common.dependencies.fill_loged_user_context_dependency import (
    fill_loged_user_context_dependency,
)
from app.common.dependencies.verify_loged_user_dependency import (
    verify_loged_user_dependency,
)
from app.models.obj_user_model import ObjUserModel
from app.routing import calendar_routing
from app.routing import user_calendar_routing
from app.routing import auth_routing
from app.routing import user_routing
from app.routing import event_routing
from app.common.db_connection import SessionDep, create_db_and_tables
from app.schemas.obj_user_schema import ObjUserSchemaComplete

app = FastAPI(title="Self Calendar Api", version="0.0.1", dependencies=[])

app.include_router(
    calendar_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
        Depends(fill_loged_user_context_dependency),
    ],
)
app.include_router(
    user_calendar_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
        Depends(fill_loged_user_context_dependency),
    ],
)
app.include_router(
    user_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
        Depends(fill_loged_user_context_dependency),
    ],
)
app.include_router(
    event_routing.router,
    dependencies=[
        Depends(verify_loged_user_dependency),
        Depends(fill_loged_user_context_dependency),
    ],
)
app.include_router(auth_routing.router)

create_db_and_tables()


# TODO debug
@db_session_injector
def create_user(db_session: SessionDep):
    user = ObjUserSchemaComplete(
        id="test", login="test", hashed_password="test"
    )
    db_calendar = ObjUserModel.model_validate(user)
    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)


# create_user()
