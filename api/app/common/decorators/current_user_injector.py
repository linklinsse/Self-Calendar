from functools import wraps
from typing import Annotated

from fastapi import Depends, Request


import app.common.security as security

from app.schemas.obj_user_schema import ObjUserSchemaComplete
from app.services.obj_user_service import get_user

def current_user_injector(func):
    """Injecte automatiquement user depuis le token"""

    @wraps(func)
    def wrapper(*args, **kwargs):

        # token: Annotated[str, Depends(security.oauth2_scheme)]
        test = Depends(security.oauth2_scheme)
        print(test)
        # test = Depends(Request)
        # print('token 1', test)
        # test_2 = Depends(security.oauth2_scheme)
        # print('token 2', test_2)
        # print('token 3', test_2)

        token = "test"
        user = get_user(token)
        if user:
            kwargs['user'] = user
        return func(*args, **kwargs)
    return wrapper

@current_user_injector
def get_current_user(user: ObjUserSchemaComplete) -> ObjUserSchemaComplete:
    return user