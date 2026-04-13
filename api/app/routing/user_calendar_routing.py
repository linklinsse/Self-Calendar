from typing import List
from fastapi import APIRouter

from app.common.db_connection import SessionDep
from app.services import lnk_user_calendar_service
from app.schemas.lnk_user_calendar_schema import (
    LnkUserCalendarSchemaComplete,
    LnkUserCalendarSchemaCreate,
    LnkUserCalendarSchemaEdit,
)

router = APIRouter(prefix="/user_calendar", tags=["user_calendar"])


@router.post("/", response_model=LnkUserCalendarSchemaComplete)
async def create(
    new_membership: LnkUserCalendarSchemaCreate, session: SessionDep
) -> LnkUserCalendarSchemaComplete:
    """Add a user to a calendar. Requires Owner ("O") permission."""
    return lnk_user_calendar_service.create_lnk_user_calendar(new_membership, session)


@router.get("/all/{calendar_id}", response_model=List[LnkUserCalendarSchemaComplete])
async def get_all(
    calendar_id: str, session: SessionDep
) -> List[LnkUserCalendarSchemaComplete]:
    """List all members of a calendar. Requires at least read ("R") permission."""
    return lnk_user_calendar_service.get_all_lnk_user_calendar(calendar_id, session)


@router.get("/{membership_id}", response_model=LnkUserCalendarSchemaComplete)
async def get(
    membership_id: str, session: SessionDep
) -> LnkUserCalendarSchemaComplete:
    """Get a single user–calendar membership by ID."""
    return lnk_user_calendar_service.get_lnk_user_calendar(membership_id, session)


@router.patch("/{membership_id}", response_model=LnkUserCalendarSchemaComplete)
async def patch(
    membership_id: str,
    edited_membership: LnkUserCalendarSchemaEdit,
    session: SessionDep,
) -> LnkUserCalendarSchemaComplete:
    """Update the permission level of an existing membership. Requires Owner ("O")."""
    return lnk_user_calendar_service.edit_lnk_user_calendar(
        membership_id, edited_membership, session
    )


@router.delete("/{membership_id}")
async def delete(membership_id: str, session: SessionDep):
    """Remove a user from a calendar. Requires Owner ("O") permission."""
    return lnk_user_calendar_service.delete_lnk_user_calendar(membership_id, session)
