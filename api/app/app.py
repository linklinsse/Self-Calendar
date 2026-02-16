from fastapi import Depends, FastAPI

from app.common.decorators.db_session_injector import db_session_injector
from app.common.dependencies.verif_loged_user_middleware import verify_token
from app.models.obj_user_model import ObjUserModel
from app.routing import calendar_routing
from app.routing import user_calendar_routing
from app.routing import auth_routing
from app.routing import user_routing
from app.common.db_connection import SessionDep, create_db_and_tables
from app.schemas.obj_user_schema import ObjUserSchemaComplete

app = FastAPI(
    title="Self Calendar Api", 
    version="0.0.1",
    dependencies=[Depends(verify_token)]
)

app.include_router(calendar_routing.router)
app.include_router(user_calendar_routing.router)
app.include_router(user_routing.router)
app.include_router(auth_routing.router)

create_db_and_tables()

# TODO debug
@db_session_injector
def create_user(db_session: SessionDep):
    user = ObjUserSchemaComplete(
        id='test',
        login='test',
        hashed_password='test'
    )
    db_calendar = ObjUserModel.model_validate(user)
    db_session.add(db_calendar)
    db_session.commit()
    db_session.refresh(db_calendar)

# create_user()