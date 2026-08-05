"""
app/common/enums.py
-------------------
Shared enumerations used across models, schemas, and services.

Adding a new permission level:
    1. Add a member to CalendarRight.
    2. Update right_order in verify_user_right_calendar.py.
    3. Update the permission table in README.md.
"""

from enum import Enum


class CalendarRight(str, Enum):
    """Permission levels for a user–calendar membership.

    Values are ordered: READ < WRITE < OWNER.
    A check for WRITE will also pass for an OWNER user.

    Stored as a single character in the database ("R", "W", "O") so that
    existing rows remain valid after this enum is introduced.
    """

    READ  = "R"  # Can read the calendar and its events
    WRITE = "W"  # All of READ + create / edit / delete events
    OWNER = "O"  # All of WRITE + edit / delete the calendar, manage members


class EventRecurenceType(str, Enum):
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    YEARLY = "Y"

class EventRecurenceEndType(str, Enum):
    NEVER = "N"
    COUNT = "C"
    UNTIL = "U"
