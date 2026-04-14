from typing import List
from sqlmodel import Session, select

from app.common.contexts.logged_user_context import get_logged_user_context
from app.common.errors import AppErrorCode, raise_app_error
from app.common.utils.verify_user_right_calendar import verify_user_right_calendar
from app.models.lnk_user_calendar_model import LnkUserCalendarModel
from app.models.obj_calendar_model import ObjCalendarModel
from app.models.obj_user_model import ObjUserModel
from app.schemas.lnk_user_calendar_schema import (
    LnkUserCalendarSchemaComplete,
    LnkUserCalendarSchemaCreate,
    LnkUserCalendarSchemaEdit,
)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_link_or_404(link_id: str, session: Session) -> LnkUserCalendarModel:
    """Fetch a membership record or raise 404."""
    db_link = session.get(LnkUserCalendarModel, link_id)
    if not db_link:
        raise_app_error(AppErrorCode.MEMBERSHIP_NOT_FOUND)
    return db_link


def _get_calendar_or_404(calendar_id: str, session: Session) -> ObjCalendarModel:
    """Fetch a calendar or raise 404."""
    db_calendar = session.get(ObjCalendarModel, calendar_id)
    if not db_calendar:
        raise_app_error(AppErrorCode.CALENDAR_NOT_FOUND)
    return db_calendar


def _require_owner(calendar_id: str, session: Session) -> None:
    """Raise INSUFFICIENT_RIGHTS if the current user is not an Owner."""
    db_calendar = _get_calendar_or_404(calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "O"):
        raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)


def _count_owners(calendar_id: str, session: Session) -> int:
    """Return the number of Owner-level memberships for a calendar."""
    statement = select(LnkUserCalendarModel).where(
        LnkUserCalendarModel.calendar_id == calendar_id,
        LnkUserCalendarModel.right == "O",
    )
    return len(session.exec(statement).all())


# ── Public service functions ───────────────────────────────────────────────────


def create_lnk_user_calendar(
    new_lnk_user_calendar: LnkUserCalendarSchemaCreate, session: Session
) -> LnkUserCalendarSchemaComplete:
    """Add a user to a calendar by username.

    The caller supplies a username; this service resolves it to a user record
    and raises HTTP 404 (USER_NOT_FOUND) if no such user exists.

    Permission rules:
    - The first membership of a calendar (the creator's Owner link) is always
      allowed — it is called internally by create_calendar() in the same tx.
    - Any subsequent membership requires the caller to be an Owner ("O").
    """
    # Resolve username → user
    db_user = session.exec(
        select(ObjUserModel).where(
            ObjUserModel.username == new_lnk_user_calendar.username
        )
    ).first()
    if not db_user:
        raise_app_error(AppErrorCode.USER_NOT_FOUND)

    existing = session.exec(
        select(LnkUserCalendarModel).where(
            LnkUserCalendarModel.calendar_id == new_lnk_user_calendar.calendar_id
        )
    ).first()

    # If members already exist this is an external add-member call — Owner only.
    if existing:
        _require_owner(new_lnk_user_calendar.calendar_id, session)

    # Guard against duplicate memberships.
    duplicate = session.exec(
        select(LnkUserCalendarModel).where(
            LnkUserCalendarModel.calendar_id == new_lnk_user_calendar.calendar_id,
            LnkUserCalendarModel.user_id == db_user.id,
        )
    ).first()
    if duplicate:
        raise_app_error(AppErrorCode.MEMBERSHIP_ALREADY_EXISTS)

    db_link = LnkUserCalendarModel(
        user_id=db_user.id,
        calendar_id=new_lnk_user_calendar.calendar_id,
        right=new_lnk_user_calendar.right,
    )
    session.add(db_link)
    session.commit()
    session.refresh(db_link)
    return db_link


def get_lnk_user_calendar(
    lnk_user_calendar_id: str, session: Session
) -> LnkUserCalendarSchemaComplete:
    """Fetch a single user–calendar membership record by its ID."""
    return _get_link_or_404(lnk_user_calendar_id, session)


def get_all_lnk_user_calendar(
    calendar_id: str, session: Session
) -> List[LnkUserCalendarSchemaComplete]:
    """Return all membership records for a given calendar.

    Requires at least read ("R") permission on the calendar.
    """
    db_calendar = _get_calendar_or_404(calendar_id, session)
    if not verify_user_right_calendar(get_logged_user_context(), db_calendar, "R"):
        raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)

    return session.exec(
        select(LnkUserCalendarModel).where(
            LnkUserCalendarModel.calendar_id == calendar_id
        )
    ).all()


def edit_lnk_user_calendar(
    lnk_user_calendar_id: str,
    edited_lnk_user_calendar: LnkUserCalendarSchemaEdit,
    session: Session,
) -> LnkUserCalendarSchemaComplete:
    """Update the permission level on an existing membership.

    Requires Owner ("O") permission on the calendar.
    Prevents demoting the last Owner of a calendar.
    """
    db_link = _get_link_or_404(lnk_user_calendar_id, session)
    _require_owner(db_link.calendar_id, session)

    # Guard: cannot demote the last Owner.
    if db_link.right == "O" and edited_lnk_user_calendar.right != "O":
        if _count_owners(db_link.calendar_id, session) <= 1:
            raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)

    update_data = edited_lnk_user_calendar.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_link, key, value)

    session.add(db_link)
    session.commit()
    session.refresh(db_link)
    return db_link


def delete_lnk_user_calendar(lnk_user_calendar_id: str, session: Session) -> None:
    """Remove a user–calendar membership record.

    Requires Owner ("O") permission on the calendar.
    Prevents removing the last Owner of a calendar.
    """
    db_link = _get_link_or_404(lnk_user_calendar_id, session)
    _require_owner(db_link.calendar_id, session)

    if db_link.right == "O" and _count_owners(db_link.calendar_id, session) <= 1:
        raise_app_error(AppErrorCode.INSUFFICIENT_RIGHTS)

    session.delete(db_link)
    session.commit()
