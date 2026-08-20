"""
app/common/utils/recurrence_expansion.py
----------------------------------------
Canonical recurrence expansion.

Recurrence used to be implemented three times — here in Python (only
`compute_estimated_end`), in JavaScript (`getOccurrencesInRange` in
app/src/lib/utils.js) and again as a hand-maintained Kotlin port in the
Android widget. It drifted twice: monthly/yearly rollover semantics, and
whether an exception matches an occurrence by exact epoch or by calendar
day. A cap bug was faithfully duplicated into both clients.

This module is the single source of truth. `GET /event/range?expand=true`
serves it, the Android widget consumes that and no longer expands anything
itself, and the web client's own copy is pinned to this one by a shared
conformance fixture (see generate_conformance_fixture.py) so drift shows up
as a failing test rather than as two surfaces disagreeing about the same
database.

Timezone note: occurrences are computed in *local* civil time, matching what
both clients have always done — an event at 09:00 recurs at 09:00, not at a
fixed UTC offset, so it survives a DST boundary the way a person expects.
The API stores unix timestamps with no timezone attached, so "local" here
means the timezone the caller passes in. There is no per-event timezone
column yet (see review.md §5); until there is, the client's own timezone is
the best available answer and is sent explicitly rather than guessed.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

# Matches the clients' own cap. Retained as a guard against a malformed rule
# producing an unbounded loop, not as a functional limit: _fast_forward_to
# means a legitimate range never approaches it.
SAFETY_ITERATIONS = 1500

# API day bitmask is Monday-first ("1000000" = Monday).
_BITMASK_LENGTH = 7


def resolve_timezone(name: str | None) -> tzinfo:
    """Client timezone, falling back to UTC on anything unusable."""
    if not name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo("UTC")


def _to_local(epoch: int, tz: tzinfo) -> datetime:
    return datetime.fromtimestamp(epoch, tz=tz)


def _midnight(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _days_between(later: datetime, earlier: datetime) -> int:
    """Whole days from *earlier* to *later*, by calendar day.

    Deliberately date arithmetic rather than a seconds division: across a DST
    boundary a "day" is 23 or 25 hours, and dividing by 86400 would silently
    drop or double a day.
    """
    return (_midnight(later).date() - _midnight(earlier).date()).days


def _selected_weekdays(days: str | None) -> list[int]:
    """Monday-first bitmask -> Python weekday indices (Mon=0 .. Sun=6)."""
    if not days or len(days) != _BITMASK_LENGTH:
        return []
    return [i for i, flag in enumerate(days) if flag == "1"]


def _add_days(dt: datetime, days: int) -> datetime:
    """Add days in civil time, preserving wall-clock time across DST.

    `dt + timedelta(days=n)` on an aware datetime adds exact elapsed time, so
    a 09:00 event lands on 08:00 or 10:00 after a DST transition. Rebuilding
    the datetime from the shifted date keeps the wall clock, which is what a
    recurring event means to a person.
    """
    naive = dt.replace(tzinfo=None) + timedelta(days=days)
    return naive.replace(tzinfo=dt.tzinfo)


def _set_ymd(dt: datetime, year: int, month: int, day: int) -> datetime:
    naive = dt.replace(tzinfo=None).replace(year=year, month=month, day=day)
    return naive.replace(tzinfo=dt.tzinfo)


def _next_occurrence(current: datetime, rec: dict) -> datetime | None:
    """The next occurrence strictly after *current*, or None if the rule ends.

    Monthly and yearly follow RFC 5545 *skip* semantics: a target month that
    does not have the anchor day-of-month (the 31st, or Feb 29) is skipped
    entirely rather than rolled over into the next month or clamped to the
    month's last day. Both clients were aligned to this in 2026-07-28, and
    `rrule.js`'s export path assumes it — changing it here makes exported
    events disagree with what the app displays.
    """
    interval = max(1, int(rec.get("interval") or 1))
    rec_type = rec.get("type")

    if rec_type == "D":
        return _add_days(current, interval)

    if rec_type == "W":
        selected = _selected_weekdays(rec.get("days"))
        if selected:
            current_dow = current.weekday()
            later = [d for d in selected if d > current_dow]
            if later:
                return _add_days(current, later[0] - current_dow)
            # Wrap to the first selected day of the next active week.
            return _add_days(
                current,
                (7 - current_dow + selected[0]) + (interval - 1) * 7,
            )
        return _add_days(current, 7 * interval)

    if rec_type == "M":
        anchor_day = current.day
        total_months = current.year * 12 + (current.month - 1)
        for _ in range(SAFETY_ITERATIONS):
            total_months += interval
            year, month = divmod(total_months, 12)
            month += 1
            if monthrange(year, month)[1] >= anchor_day:
                return _set_ymd(current, year, month, anchor_day)
        return None

    if rec_type == "Y":
        anchor_day, anchor_month = current.day, current.month
        year = current.year
        for _ in range(SAFETY_ITERATIONS):
            year += interval
            if monthrange(year, anchor_month)[1] >= anchor_day:
                return _set_ymd(current, year, anchor_month, anchor_day)
        return None

    return None


def _fast_forward_to(
    current: datetime, rec: dict, range_start: datetime, count: int
) -> tuple[datetime, int]:
    """Skip to the last occurrence at or before *range_start* in O(1).

    Stepping one occurrence at a time from the event's start made cost
    proportional to the event's *age* rather than the range being drawn, and
    the safety cap then truncated silently — a daily event stopped rendering
    entirely once it passed ~4.1 years old.

    Only daily and weekly are fast-forwarded. Monthly and yearly produce at
    most 12 and 1 a year, so stepping them is already cheap, and their skip
    semantics make the occurrence count non-uniform — extrapolating it would
    corrupt the running count that endType="C" depends on.
    """
    interval = max(1, int(rec.get("interval") or 1))
    rec_type = rec.get("type")
    end_type = rec.get("endType")
    limit = rec.get("count")

    gap_days = _days_between(range_start, current)
    if gap_days <= 0:
        return current, count

    if rec_type == "D":
        steps = gap_days // interval
        if end_type == "C" and limit is not None:
            steps = min(steps, max(0, limit - count - 1))
        if steps <= 0:
            return current, count
        return _add_days(current, steps * interval), count + steps

    if rec_type == "W":
        selected = _selected_weekdays(rec.get("days"))

        # The pattern is periodic with period 7*interval days, but only once
        # `current` sits on a selected weekday: an "every Tuesday" rule whose
        # start date is a Monday emits that Monday first. Extrapolating from
        # that irregular first cycle overstates the rate and drops
        # count-limited series entirely. _next_occurrence always lands on a
        # selected day when days is non-empty, so this is at most one step.
        if selected and current.weekday() not in selected:
            if end_type == "C" and limit is not None and count + 1 >= limit:
                return current, count
            stepped = _next_occurrence(current, rec)
            if stepped is None:
                return current, count
            current, count = stepped, count + 1

        per_cycle = len(selected) if selected else 1
        cycle_days = 7 * interval
        cycles = _days_between(range_start, current) // cycle_days
        if end_type == "C" and limit is not None:
            remaining = max(0, limit - count - 1)
            cycles = min(cycles, remaining // per_cycle)
        if cycles <= 0:
            return current, count
        return (
            _add_days(current, cycles * cycle_days),
            count + cycles * per_cycle,
        )

    return current, count


def occurrences_in_range(
    date_start: int,
    date_end: int,
    rec: dict,
    range_start: int,
    range_end: int,
    tz: tzinfo,
) -> list[int]:
    """Occurrence start epochs for a recurring event overlapping the range.

    An occurrence is included when it *overlaps* the range, so a multi-day
    event that began before `range_start` and is still running is returned —
    dropping it would make long events vanish from views they visibly cross.
    """
    if not rec or not rec.get("type"):
        return []

    base = _midnight(_to_local(date_start, tz))
    base_end = _midnight(_to_local(date_end, tz))
    span_days = (base_end.date() - base.date()).days

    local_range_start = _midnight(_to_local(range_start, tz))
    local_range_end = _midnight(_to_local(range_end, tz))

    until_midnight = None
    if rec.get("endType") == "U" and rec.get("until") is not None:
        until_midnight = _midnight(_to_local(rec["until"], tz))

    results: list[int] = []
    current = base
    count = 0

    current, count = _fast_forward_to(current, rec, local_range_start, count)

    for _ in range(SAFETY_ITERATIONS):
        if until_midnight is not None and _midnight(current) > until_midnight:
            break
        if rec.get("endType") == "C" and count >= (rec.get("count") or 0):
            break
        if _midnight(current) > local_range_end:
            break

        occurrence_end = _add_days(current, span_days)
        if _midnight(occurrence_end) >= local_range_start:
            results.append(int(current.timestamp()))
        count += 1

        nxt = _next_occurrence(current, rec)
        if nxt is None:
            break
        current = nxt

    return results


def expand_events(
    events: list,
    range_start: int,
    range_end: int,
    timezone_name: str | None,
) -> list[dict]:
    """Expand events into one entry per occurrence within the range.

    Non-recurring events pass through when they overlap the range. Recurring
    events are expanded and their excluded occurrences removed.

    Exclusions are matched by calendar *day*, not exact epoch. The web client
    writes them as local midnight while the Google importer writes the
    occurrence's real instant; requiring an exact match made imported
    exclusions silent no-ops on one surface and effective on another.
    """
    tz = resolve_timezone(timezone_name)
    out: list[dict] = []

    local_range_start = _midnight(_to_local(range_start, tz))
    local_range_end = _midnight(_to_local(range_end, tz))

    for event in events:
        span_seconds = event.date_end - event.date_start
        recurrence = getattr(event, "obj_recurence", None)

        if recurrence is None:
            starts_before_end = (
                _midnight(_to_local(event.date_start, tz)) <= local_range_end
            )
            ends_after_start = (
                _midnight(_to_local(event.date_end, tz)) >= local_range_start
            )
            if starts_before_end and ends_after_start:
                out.append(
                    {
                        "event_id": event.id,
                        "date_start": event.date_start,
                        "date_end": event.date_end,
                    }
                )
            continue

        rule = {
            "type": recurrence.type,
            "interval": recurrence.interval,
            "days": recurrence.days,
            "endType": recurrence.endType,
            "count": recurrence.count,
            "until": recurrence.until,
        }

        excluded = {
            _midnight(_to_local(exception.date, tz)).date()
            for exception in (recurrence.obj_exceptions or [])
        }

        for occurrence_start in occurrences_in_range(
            event.date_start, event.date_end, rule, range_start, range_end, tz
        ):
            if _midnight(_to_local(occurrence_start, tz)).date() in excluded:
                continue
            out.append(
                {
                    "event_id": event.id,
                    "date_start": occurrence_start,
                    "date_end": occurrence_start + span_seconds,
                }
            )

    return out
