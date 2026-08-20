"""
app/common/errors.py
---------------------
Centralized error catalogue for the Self Calendar API.

Every HTTP error raised in services or routers must go through
`raise_app_error(code)`.  This keeps HTTP status codes, error codes,
and human-readable messages in a single place.

Adding a new error:
    1. Add a member to `AppErrorCode`.
    2. Add its message to `_ERROR_MESSAGES`.
    3. Add its HTTP status to `_ERROR_STATUS`.
    4. Call `raise_app_error(AppErrorCode.YOUR_NEW_CODE)` where needed.
"""

from enum import Enum
from typing import NoReturn

from fastapi import HTTPException, status


# ── 1. Error codes ───────────────────────────────────────────────────────────


class AppErrorCode(str, Enum):
    # Auth
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INVALID_TOKEN = "INVALID_TOKEN"

    # User
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    REGISTRATION_DISABLED = "REGISTRATION_DISABLED"

    # Calendar
    CALENDAR_NOT_FOUND = "CALENDAR_NOT_FOUND"

    # Event
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"

    # Recurrence
    RECURRENCE_NOT_FOUND = "RECURRENCE_NOT_FOUND"

    # Category
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"

    # Membership (lnk_user_calendar)
    MEMBERSHIP_NOT_FOUND = "MEMBERSHIP_NOT_FOUND"
    MEMBERSHIP_ALREADY_EXISTS = "MEMBERSHIP_ALREADY_EXISTS"

    # Permissions
    INSUFFICIENT_RIGHTS = "INSUFFICIENT_RIGHTS"

    # Rate limiting
    RATE_LIMITED = "RATE_LIMITED"


# ── 2. Human-readable messages ───────────────────────────────────────────────


_ERROR_MESSAGES: dict[AppErrorCode, str] = {
    AppErrorCode.INVALID_CREDENTIALS: (
        "Invalid username or password."
    ),
    AppErrorCode.INVALID_TOKEN: (
        "Authentication token is invalid or has expired."
    ),
    AppErrorCode.USER_NOT_FOUND: (
        "The requested user does not exist."
    ),
    AppErrorCode.USER_ALREADY_EXISTS: (
        "A user with this username already exists."
    ),
    AppErrorCode.REGISTRATION_DISABLED: (
        "Account registration is disabled on this server."
    ),
    AppErrorCode.CALENDAR_NOT_FOUND: (
        "The requested calendar does not exist."
    ),
    AppErrorCode.EVENT_NOT_FOUND: (
        "The requested event does not exist."
    ),
    AppErrorCode.INVALID_DATE_RANGE: (
        "The end of the range must not be before its start."
    ),
    AppErrorCode.RECURRENCE_NOT_FOUND: (
        "The requested recurrence rule does not exist."
    ),
    AppErrorCode.CATEGORY_NOT_FOUND: (
        "The requested category does not exist."
    ),
    AppErrorCode.MEMBERSHIP_NOT_FOUND: (
        "The requested membership record does not exist."
    ),
    AppErrorCode.MEMBERSHIP_ALREADY_EXISTS: (
        "This user is already a member of the calendar."
    ),
    AppErrorCode.INSUFFICIENT_RIGHTS: (
        "You do not have the required permission to perform this action."
    ),
    AppErrorCode.RATE_LIMITED: (
        "Too many failed attempts. Please try again later."
    ),
}


# ── 3. HTTP status mapping ───────────────────────────────────────────────────


_ERROR_STATUS: dict[AppErrorCode, int] = {
    AppErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    AppErrorCode.INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    AppErrorCode.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppErrorCode.USER_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    AppErrorCode.REGISTRATION_DISABLED: status.HTTP_403_FORBIDDEN,
    AppErrorCode.CALENDAR_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppErrorCode.EVENT_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppErrorCode.INVALID_DATE_RANGE: status.HTTP_422_UNPROCESSABLE_ENTITY,
    AppErrorCode.RECURRENCE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppErrorCode.CATEGORY_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppErrorCode.MEMBERSHIP_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    AppErrorCode.MEMBERSHIP_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    AppErrorCode.INSUFFICIENT_RIGHTS: status.HTTP_403_FORBIDDEN,
    AppErrorCode.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
}


# ── 4. Public helper ─────────────────────────────────────────────────────────


def raise_app_error(code: AppErrorCode) -> NoReturn:
    """Raise an HTTPException for the given AppErrorCode.

    The response body will always follow the shape::

        {
            "detail": {
                "error_code": "SOME_ERROR_CODE",
                "message": "Human-readable description."
            }
        }
    """

    raise HTTPException(
        status_code=_ERROR_STATUS[code],
        detail={
            "error_code": code.value,
            "message": _ERROR_MESSAGES[code],
        },
    )