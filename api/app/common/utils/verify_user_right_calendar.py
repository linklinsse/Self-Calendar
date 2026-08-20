from app.common.enums import CalendarRight
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_user_model import ObjUserModel

# Ordered from least to most privileged — used for >= comparisons.
_RIGHT_ORDER: list[CalendarRight] = [
    CalendarRight.READ,
    CalendarRight.WRITE,
    CalendarRight.OWNER,
]


def verify_user_right_calendar(
    db_user: ObjUserModel,
    db_calendar: ObjCalendarModel,
    needed_right: CalendarRight | str = CalendarRight.READ,
) -> bool:
    """Check whether a user holds at least the required permission on a calendar.

    Args:
        db_user:       The user whose permissions are being checked.
        db_calendar:   The calendar to check against.
        needed_right:  Minimum required permission level (CalendarRight or raw str).

    Returns:
        True if the user has the required permission level or higher,
        False otherwise (including when the user has no link to the calendar).
    """
    needed = CalendarRight(needed_right)
    needed_index = _RIGHT_ORDER.index(needed)

    for db_lnk_user in db_calendar.lnk_users:
        if db_lnk_user.user_id == db_user.id:
            user_right = CalendarRight(db_lnk_user.right)
            if _RIGHT_ORDER.index(user_right) >= needed_index:
                return True
            break  # User found but has insufficient rights — stop searching

    return False


def require_calendar_right(
    db_user: ObjUserModel,
    db_calendar: ObjCalendarModel,
    needed_right: CalendarRight | str,
) -> None:
    """Enforce a right, distinguishing "not a member" from "outranked".

    The distinction is the whole point. Returning INSUFFICIENT_RIGHTS to
    someone with no membership confirms the calendar exists, which defeats
    the anti-enumeration choice made everywhere else: `GET /calendar/{id}`
    deliberately answers 404 rather than 403 so that an outsider cannot
    probe for real ids. Several owner-only routes answered 403 instead, so
    the two could be compared — GET said "no such calendar" and PATCH said
    "you lack permission" for the same id, and the second answer is the
    true one.

    So:
        no membership at all  -> CALENDAR_NOT_FOUND (404)
        member, but outranked -> INSUFFICIENT_RIGHTS (403)

    A member already knows the calendar exists, so 403 tells them nothing
    they could not already see, and is far more useful than a 404 that
    looks like the calendar vanished.
    """
    from app.common.errors import AppErrorCode, raise_app_error

    if not verify_user_right_calendar(db_user, db_calendar, CalendarRight.READ):
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)

    if not verify_user_right_calendar(db_user, db_calendar, needed_right):
        raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)
