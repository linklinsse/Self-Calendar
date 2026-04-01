from typing import List
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_user_model import ObjUserModel

# ---------------------------------------------------------------------------
# Permission levels in ascending order of privilege:
#       "R" — Read only
#       "W" — Read/Write (can create/edit events)
#       "O" — Owner      (full control)
# ---------------------------------------------------------------------------
right_order: List[str] = ["R", "W", "O"]


def verif_user_right_calendar(
    db_user: ObjUserModel,
    db_calendar: ObjCalendarModel,
    needed_right: str = right_order[0],
) -> bool:
    """Check whether a user holds at least the required permission on a calendar.

    Args:
        db_user:       The user whose permissions are being checked.
        db_calendar:   The calendar to check against.
        needed_right:  Minimum required permission level ("R", "W", or "O").

    Returns:
        True if the user has the required permission level or higher,
        False otherwise (including when the user has no link to the calendar).
    """
    # Find the required permission level index (higher index = more privilege)
    needed_right_level = right_order.index(needed_right)

    for db_lnk_user in db_calendar.lnk_users:
        if db_lnk_user.user_id == db_user.id:
            # User found in the calendar's link table — compare privilege level
            if right_order.index(db_lnk_user.right) >= needed_right_level:
                return True
            # User exists but has insufficient rights — stop searching
            break

    # User not linked to this calendar, or has insufficient rights
    return False
