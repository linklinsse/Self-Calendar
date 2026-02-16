from functools import wraps


# TODO
def user_calendar_right_guard(right: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get("user")
            if user:
                kwargs["user_id"] = user.id
            return func(*args, **kwargs)

        return wrapper
