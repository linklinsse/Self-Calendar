from functools import wraps


def db_session_injector(func):
    """Decorator — automatically inject a database session into a function.

    Usage:
        @db_session_injector
        def my_service_function(some_arg: str, db_session: SessionDep):
            ...

    The decorated function must declare `db_session` as a keyword argument.
    A fresh session is obtained from get_session() and passed automatically,
    so callers do not need to supply it.

    Note: This is used in service functions that are called outside of a
    FastAPI request context (e.g. scripts, tests). Inside request handlers
    the standard `SessionDep` FastAPI dependency is preferred.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        from app.common.db_connection import get_session

        # get_session() is a generator; advance it once to obtain the session
        db_session = get_session()
        db_session_value = next(db_session)
        kwargs["db_session"] = db_session_value
        return func(*args, **kwargs)

    return wrapper
