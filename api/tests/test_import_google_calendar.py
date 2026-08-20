"""
Tests for the pure parsing/mapping helpers in
scripts/import_google_calendar.py.

None of these touch the network or the database — they are the functions
that decide what a Google event *means*, which is where the importer's bugs
live. The script's own module docstring calls out its deliberate
simplifications; these tests pin the parts that are supposed to be exact.

Skipped unless the google-import extra is installed:
    uv sync --extra google-import
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

pytest.importorskip("googleapiclient", reason="google-import extra not installed")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import import_google_calendar as importer  # noqa: E402

PARIS = ZoneInfo("Europe/Paris")
NEW_YORK = ZoneInfo("America/New_York")


def epoch(dt: datetime) -> int:
    return int(dt.timestamp())


# ── Timezone anchoring ───────────────────────────────────────────────────


def test_all_day_dates_are_anchored_to_the_calendar_timezone():
    """A Google all-day event is "the 4th" in the calendar's own timezone,
    not in UTC. Anchoring to UTC shifted every all-day event onto the wrong
    day for anyone not on UTC."""
    got = importer.parse_google_datetime({"date": "2026-03-04"}, PARIS)
    assert got == epoch(datetime(2026, 3, 4, 0, 0, tzinfo=PARIS))

    got_ny = importer.parse_google_datetime({"date": "2026-03-04"}, NEW_YORK)
    assert got_ny == epoch(datetime(2026, 3, 4, 0, 0, tzinfo=NEW_YORK))

    assert got != got_ny


def test_timed_values_carry_their_own_offset():
    """dateTime values are absolute, so the calendar timezone is irrelevant."""
    field = {"dateTime": "2026-03-04T09:00:00+01:00"}
    assert importer.parse_google_datetime(field, PARIS) == importer.parse_google_datetime(
        field, NEW_YORK
    )
    assert importer.parse_google_datetime(field, PARIS) == epoch(
        datetime(2026, 3, 4, 8, 0, tzinfo=timezone.utc)
    )


def test_resolve_timezone_falls_back_to_utc():
    assert importer.resolve_timezone(None) is timezone.utc
    assert importer.resolve_timezone("Not/AZone") is timezone.utc
    assert importer.resolve_timezone("Europe/Paris") == PARIS


# ── Excluded occurrences ─────────────────────────────────────────────────


def test_exclusions_are_normalised_to_midnight():
    """Both clients match exceptions to occurrences by calendar day, and the
    web app writes them as midnight of that day. Storing a raw instant made
    every imported EXDATE and cancelled override a silent no-op: the
    cancelled occurrence still rendered, and a modified one rendered twice."""
    instant = epoch(datetime(2026, 3, 4, 9, 30, tzinfo=PARIS))
    assert importer.to_exclusion_epoch(instant, PARIS) == epoch(
        datetime(2026, 3, 4, 0, 0, tzinfo=PARIS)
    )


def test_exdates_come_back_as_midnight_epochs():
    fields, exceptions = importer.analyze_recurrence(
        ["RRULE:FREQ=WEEKLY;BYDAY=WE", "EXDATE;TZID=Europe/Paris:20260311T093000"],
        epoch(datetime(2026, 3, 4, 9, 30, tzinfo=PARIS)),
        PARIS,
    )
    assert fields["type"] == "W"
    assert exceptions == [epoch(datetime(2026, 3, 11, 0, 0, tzinfo=PARIS))]


# ── Recurrence mapping ───────────────────────────────────────────────────


def test_weekly_without_byday_uses_the_calendar_timezone_weekday():
    """An event at 00:30 Paris time on a Wednesday is still Tuesday in UTC.
    This used to call fromtimestamp() with no tz at all, so the weekday
    depended on where the import happened to be run."""
    start = epoch(datetime(2026, 3, 4, 0, 30, tzinfo=PARIS))  # Wednesday in Paris
    fields, _ = importer.analyze_recurrence(["RRULE:FREQ=WEEKLY"], start, PARIS)
    # days is a Monday-first bitmask: Wednesday is index 2.
    assert fields["days"] == "0010000"


def test_byday_maps_to_a_monday_first_bitmask():
    fields, _ = importer.analyze_recurrence(
        ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"], 0, timezone.utc
    )
    assert fields["days"] == "1010100"


def test_count_and_until_map_to_end_types():
    fields, _ = importer.analyze_recurrence(
        ["RRULE:FREQ=DAILY;COUNT=10"], 0, timezone.utc
    )
    assert (fields["endType"], fields["count"], fields["until"]) == ("C", 10, None)

    fields, _ = importer.analyze_recurrence(
        ["RRULE:FREQ=DAILY;UNTIL=20260630T000000Z"], 0, timezone.utc
    )
    assert fields["endType"] == "U"
    assert fields["until"] == epoch(datetime(2026, 6, 30, tzinfo=timezone.utc))

    fields, _ = importer.analyze_recurrence(["RRULE:FREQ=DAILY"], 0, timezone.utc)
    assert (fields["endType"], fields["count"], fields["until"]) == ("N", None, None)


@pytest.mark.parametrize(
    "lines",
    [
        ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"],       # unsupported key
        ["RRULE:FREQ=MONTHLY;BYDAY=2MO"],           # ordinal BYDAY
        ["RRULE:FREQ=MONTHLY;BYDAY=MO"],            # BYDAY on a non-weekly rule
        ["RRULE:FREQ=HOURLY"],                      # unsupported frequency
        ["RRULE:FREQ=DAILY", "RRULE:FREQ=WEEKLY"],  # multiple rules
        ["RDATE:20260304T090000Z"],                 # no equivalent
        ["RRULE:FREQ=DAILY;COUNT=5;UNTIL=20260630T000000Z"],  # invalid per RFC5545
    ],
)
def test_rules_too_complex_to_map_return_none(lines):
    """Returning None is the signal to fall back to per-instance expansion,
    so a false positive here silently drops occurrences."""
    assert importer.analyze_recurrence(lines, 0, timezone.utc) is None


# ── Field limits ─────────────────────────────────────────────────────────


def test_long_descriptions_are_truncated_rather_than_aborting_the_import():
    """CommonFieldDescription caps at 2000 chars. Google descriptions blow
    past that routinely (videoconference boilerplate, agendas), and since
    every create_event commits individually, a ValidationError partway
    through leaves a half-imported calendar that the script cannot resume."""
    assert importer.truncate_description(None) is None
    assert importer.truncate_description("short") == "short"

    long_text = "x" * 5000
    got = importer.truncate_description(long_text)
    assert len(got) == importer.MAX_DESCRIPTION_CHARS
    assert got.endswith("\u2026")


def test_event_payload_truncates_title_and_description():
    payload = importer.build_event_payload(
        "cal-1",
        {"summary": "s" * 400, "description": "d" * 5000, "location": "Paris"},
        "cat-1",
        0,
        3600,
    )
    assert len(payload.title) == 255
    assert len(payload.description) == importer.MAX_DESCRIPTION_CHARS


def test_reminder_uses_the_first_override_only():
    assert (
        importer.extract_reminder(
            {"reminders": {"overrides": [{"minutes": 15}, {"minutes": 60}]}}
        )
        == "15m"
    )
    assert importer.extract_reminder({"reminders": {"useDefault": True}}) is None
    assert importer.extract_reminder({}) is None
