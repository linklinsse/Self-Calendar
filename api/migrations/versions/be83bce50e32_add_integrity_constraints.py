"""add integrity constraints

Revision ID: be83bce50e32
Revises: 1ec329c28cf4
Create Date: 2026-08-02

Adds the three constraints that were blocked on having no migration tool:

  1. lnk_user_calendar (user_id, calendar_id) UNIQUE
  2. obj_event.recurence_id UNIQUE
  3. obj_event.category_id FOREIGN KEY -> obj_category.id

Each corresponds to a bug currently prevented by exactly one service
function, which would return the moment any other write path appeared. The
point of a constraint is that it holds regardless of which code did the
writing.

The upgrade repairs existing data before applying each constraint. A
database that predates them can genuinely contain violations — duplicate
memberships from the check-then-act race in create_lnk_user_calendar, a
shared recurrence from the period when recurence_id was client-settable, an
orphaned category_id from before delete_category cleaned up. A migration
that simply fails on real data, after the operator has taken the service
down, is not much use.

Every repair is logged rather than done silently: a database being quietly
edited during a migration should leave a trail.
"""

import logging
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel  # noqa: F401  (see script.py.mako)
from alembic import op

revision: str = "be83bce50e32"
down_revision: Union[str, Sequence[str], None] = "1ec329c28cf4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger("alembic.runtime.migration")


def _repair_duplicate_memberships(conn) -> None:
    """Collapse duplicate (user_id, calendar_id) rows, keeping the strongest.

    Strongest right rather than newest or first: these duplicates arise from
    a race, so their order carries no intent, and silently demoting someone
    who can currently administer a calendar is a worse surprise than leaving
    them able to.
    """
    duplicates = conn.execute(
        sa.text(
            """
            SELECT user_id, calendar_id, COUNT(*) AS n
            FROM lnk_user_calendar
            GROUP BY user_id, calendar_id
            HAVING n > 1
            """
        )
    ).fetchall()

    for user_id, calendar_id, count in duplicates:
        rows = conn.execute(
            sa.text(
                """
                SELECT id, "right" FROM lnk_user_calendar
                WHERE user_id = :u AND calendar_id = :c
                """
            ),
            {"u": user_id, "c": calendar_id},
        ).fetchall()

        rank = {"R": 0, "W": 1, "O": 2}
        keep = max(rows, key=lambda r: rank.get(r[1], -1))
        log.warning(
            "Collapsing %d duplicate memberships for user %s on calendar %s; "
            "keeping right=%s",
            count, user_id, calendar_id, keep[1],
        )
        for row in rows:
            if row[0] != keep[0]:
                conn.execute(
                    sa.text("DELETE FROM lnk_user_calendar WHERE id = :i"),
                    {"i": row[0]},
                )


def _repair_shared_recurrences(conn) -> None:
    """Detach all but one event from a recurrence shared between events.

    Reachable while recurence_id was client-settable: a user could point
    their own event at someone else's recurrence. Keeps the oldest holder by
    rowid — for the cross-account case that is the original owner's event,
    which is the one that should retain its rule.

    Detached events lose their recurrence and become one-off events at their
    existing start time. That is a visible change, hence the warning; the
    alternative is duplicating the rule, which would silently double a
    user's calendar entries.
    """
    shared = conn.execute(
        sa.text(
            """
            SELECT recurence_id, COUNT(*) AS n
            FROM obj_event
            WHERE recurence_id IS NOT NULL
            GROUP BY recurence_id
            HAVING n > 1
            """
        )
    ).fetchall()

    for recurrence_id, count in shared:
        rows = conn.execute(
            sa.text(
                """
                SELECT id FROM obj_event
                WHERE recurence_id = :r ORDER BY rowid
                """
            ),
            {"r": recurrence_id},
        ).fetchall()
        keep = rows[0][0]
        log.warning(
            "Recurrence %s is shared by %d events; keeping it on %s and "
            "detaching the rest (they become one-off events)",
            recurrence_id, count, keep,
        )
        for (event_id,) in rows[1:]:
            conn.execute(
                sa.text(
                    "UPDATE obj_event SET recurence_id = NULL WHERE id = :i"
                ),
                {"i": event_id},
            )


def _repair_orphaned_categories(conn) -> None:
    """Null out category_id values pointing at a category that is gone.

    This is what delete_category now does at the service level; any orphan
    still present predates that fix.
    """
    result = conn.execute(
        sa.text(
            """
            UPDATE obj_event SET category_id = NULL
            WHERE category_id IS NOT NULL
              AND category_id NOT IN (SELECT id FROM obj_category)
            """
        )
    )
    if result.rowcount:
        log.warning(
            "Cleared %d orphaned category_id reference(s) on obj_event",
            result.rowcount,
        )


def upgrade() -> None:
    conn = op.get_bind()

    _repair_duplicate_memberships(conn)
    _repair_shared_recurrences(conn)
    _repair_orphaned_categories(conn)

    # batch_alter_table rebuilds the table, which is the only way SQLite can
    # add a constraint to an existing one. Constraints are named explicitly:
    # an unnamed constraint cannot be dropped again on SQLite, so leaving
    # them anonymous would make downgrade() impossible to write.
    with op.batch_alter_table("lnk_user_calendar", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_user_calendar", ["user_id", "calendar_id"]
        )

    with op.batch_alter_table("obj_event", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_event_recurence_id", ["recurence_id"]
        )
        batch_op.create_foreign_key(
            "fk_event_category_id", "obj_category", ["category_id"], ["id"]
        )


def downgrade() -> None:
    # Only the constraints are reversible. The data repairs are not: a
    # deleted duplicate membership and a detached recurrence cannot be
    # reconstructed from what remains. Restore a backup if a downgrade is
    # meant to undo those too.
    with op.batch_alter_table("obj_event", schema=None) as batch_op:
        batch_op.drop_constraint("fk_event_category_id", type_="foreignkey")
        batch_op.drop_constraint("uq_event_recurence_id", type_="unique")

    with op.batch_alter_table("lnk_user_calendar", schema=None) as batch_op:
        batch_op.drop_constraint("uq_user_calendar", type_="unique")
