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
