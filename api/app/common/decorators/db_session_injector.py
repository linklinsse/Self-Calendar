from functools import wraps


def db_session_injector(func):
    """Injecte automatiquement une session DB"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        from app.common.db_connection import get_session

        db_session = get_session()
        db_session_value = next(db_session)
        kwargs["db_session"] = db_session_value
        return func(*args, **kwargs)

    return wrapper
