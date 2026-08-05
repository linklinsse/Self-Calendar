"""
scripts/import_google_calendar.py
----------------------------------
One-off import of a Google account's *primary* calendar into Self Calendar.

Creates a new calendar named "Google <account email>" (owned by an existing
Self Calendar user), one category per Google event color actually used, and
one event per Google event.

Setup (one time):
    1. In Google Cloud Console, create/select a project and enable the
       "Google Calendar API".
    2. Under "APIs & Services > Credentials", create an OAuth client ID of
       type "Desktop app" and download its JSON.
    3. Save it as scripts/credentials.json (or pass --credentials).

Usage (run from the api/ directory, with the google-import extra installed
via `uv sync --extra google-import`):

    uv run python scripts/import_google_calendar.py --username alice

The first run opens a browser for the Google OAuth consent screen and caches
the resulting token in scripts/token.json (or --token) for later runs.

Notes / deliberate simplifications:
- Only the account's primary calendar is imported, not secondary/shared ones.
- Google's recurrence rules (RRULE) are mapped on a best-effort basis onto
  Self Calendar's much simpler recurrence model (single daily/weekly/monthly/
  yearly interval, weekly BYDAY only). Anything more elaborate (BYMONTHDAY,
  BYSETPOS, "2nd Monday" style BYDAY, multiple RRULEs, RDATE, ...) is instead
  expanded into individual, non-recurring events via the Calendar API's
  instances() endpoint, capped at MAX_EXPANDED_INSTANCES occurrences.
- All-day ("date"-only) values are interpreted as midnight *in the Google
  calendar's own timezone*, which is how Google itself renders them and how
  a user in that timezone sees them locally. Timed ("dateTime") values carry
  their own real UTC offset, so those are exact either way.
- Excluded occurrences (EXDATE, cancelled overrides) are stored as midnight
  in that same timezone, matching how the web app writes them
  (excludeOccurrence in app/src/lib/services/event.service.js) and how both
  clients match them back (by calendar day).
- Only the first reminder override is imported, as "<n>m"; Self Calendar has
  a single free-text reminder field. `useDefault` reminders are ignored.
- Not idempotent: re-running this script imports everything again into a
  brand-new calendar rather than updating/deduplicating a previous import.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.auth.transport.requests import Request  # noqa: E402
from google.oauth2.credentials import Credentials  # noqa: E402
from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

import app.services.obj_calendar_service as obj_calendar_service  # noqa: E402
import app.services.obj_category_service as obj_category_service  # noqa: E402
import app.services.obj_event_service as obj_event_service  # noqa: E402
from app.common.contexts.logged_user_context import set_logged_user_context  # noqa: E402
from app.common.db_connection import create_db_and_tables, db_engine  # noqa: E402
from app.models.obj_user_model import ObjUserModel  # noqa: E402
from app.schemas.obj_calendar_schema import ObjCalendarSchemaCreate  # noqa: E402
from app.schemas.obj_category_schema import ObjCategorySchemaCreate  # noqa: E402
from app.schemas.obj_event_recurence_schema import (  # noqa: E402
    ObjEventRecurenceSchemaCreate,
)
from app.schemas.obj_event_schema import ObjEventSchemaCreate  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Stable, publicly documented Google Calendar event color names (the API
# itself only returns hex codes by id, never names).
GOOGLE_EVENT_COLOR_NAMES = {
    "1": "Lavender",
    "2": "Sage",
    "3": "Grape",
    "4": "Flamingo",
    "5": "Banana",
    "6": "Tangerine",
    "7": "Peacock",
    "8": "Graphite",
    "9": "Blueberry",
    "10": "Basil",
    "11": "Tomato",
}

DAY_CODE_TO_BIT_INDEX = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
UNSUPPORTED_RRULE_KEYS = {
    "BYMONTHDAY", "BYSETPOS", "BYWEEKNO", "BYYEARDAY",
    "BYMONTH", "BYHOUR", "BYMINUTE", "BYSECOND",
}
MAX_EXPANDED_INSTANCES = 2000

# Self Calendar caps event descriptions (see CommonFieldDescription in
# app/schemas/common_fields.py). Google's routinely blow past it — any
# invite carrying videoconference boilerplate or an agenda does. Truncating
# is the difference between importing such an event and aborting the whole
# run on a ValidationError partway through.
MAX_DESCRIPTION_CHARS = 2000

# instances() with no window returns occurrences indefinitely for an
# unbounded rule, relying entirely on MAX_EXPANDED_INSTANCES to stop — after
# having created up to that many rows. Bound the query itself instead.
EXPANSION_WINDOW_YEARS_BACK = 5
EXPANSION_WINDOW_YEARS_FORWARD = 5


# ── Google OAuth ──────────────────────────────────────────────────────────────


def get_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print(f"Missing OAuth client file: {credentials_path}")
                print(
                    "Create one in Google Cloud Console > APIs & Services > "
                    "Credentials > Create OAuth client ID > Desktop app, "
                    "enable the Calendar API, and download it there."
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return creds


# ── Date / recurrence parsing ────────────────────────────────────────────────


def resolve_timezone(name: str | None) -> ZoneInfo | timezone:
    """The Google calendar's own timezone, falling back to UTC.

    Everything date-only is anchored to this: it is the zone Google renders
    the calendar in, so it is also the zone a user of that calendar sees
    "all day on the 4th" in. Anchoring to UTC instead shifts every all-day
    event by a day for anyone west of Greenwich.
    """
    if not name:
        return timezone.utc
    try:
        return ZoneInfo(name)
    except Exception:
        print(f"  Warning: unknown calendar timezone {name!r}, falling back to UTC.")
        return timezone.utc


def parse_google_datetime(field: dict, cal_tz: ZoneInfo | timezone) -> int:
    """Convert a Google {'dateTime': ...} or {'date': ...} field to a unix epoch."""
    if "dateTime" in field:
        return int(datetime.fromisoformat(field["dateTime"]).timestamp())
    dt = datetime.strptime(field["date"], "%Y-%m-%d").replace(tzinfo=cal_tz)
    return int(dt.timestamp())


def ics_value_to_epoch(
    value: str, tzid: str | None, cal_tz: ZoneInfo | timezone
) -> int:
    """Convert a raw RFC5545 date/date-time value (as used in RRULE UNTIL and
    EXDATE) to a unix epoch, matching parse_google_datetime's conventions."""
    if "T" not in value:
        dt = datetime.strptime(value, "%Y%m%d").replace(tzinfo=cal_tz)
        return int(dt.timestamp())
    if value.endswith("Z"):
        dt = datetime.strptime(value[:-1], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
        dt = dt.replace(tzinfo=ZoneInfo(tzid) if tzid else cal_tz)
    return int(dt.timestamp())


def to_exclusion_epoch(epoch: int, cal_tz: ZoneInfo | timezone) -> int:
    """Normalise an occurrence instant to the excluded-occurrence convention.

    Both clients match exceptions to occurrences by calendar day, and the web
    app writes them as midnight of that day (excludeOccurrence sends the
    occurrence start, and expanded occurrences are always local midnight).
    Writing a raw instant here instead — 09:00 on the day, say — produced
    exception rows that no client could line up with an occurrence, so every
    imported EXDATE and every cancelled override was silently a no-op: the
    cancelled occurrence still showed, and a modified one showed twice.
    """
    dt = datetime.fromtimestamp(epoch, tz=cal_tz)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp())


def parse_ics_line(line: str) -> tuple[str, dict[str, str], str]:
    head, _, value = line.partition(":")
    segments = head.split(";")
    prop = segments[0].upper()
    params = {}
    for seg in segments[1:]:
        if "=" in seg:
            k, v = seg.split("=", 1)
            params[k.upper()] = v
    return prop, params, value


def parse_rrule_params(rrule_value: str) -> dict[str, str]:
    out = {}
    for part in rrule_value.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.upper()] = v
    return out


def analyze_recurrence(
    recurrence_lines: list[str],
    event_start_epoch: int,
    cal_tz: ZoneInfo | timezone,
) -> tuple[dict, list[int]] | None:
    """Best-effort map a Google 'recurrence' array onto Self Calendar's
    recurrence model. Returns None if the rule is too complex to represent
    (caller should then fall back to per-instance expansion)."""
    rrule_values = []
    exdate_entries: list[tuple[str, str | None]] = []

    for line in recurrence_lines:
        prop, params, value = parse_ics_line(line)
        if prop == "RRULE":
            rrule_values.append(value)
        elif prop == "EXDATE":
            tzid = params.get("TZID")
            exdate_entries.extend((v, tzid) for v in value.split(","))
        else:
            # RDATE / EXRULE (or anything unrecognized) have no equivalent here.
            return None

    if len(rrule_values) != 1:
        return None

    params = parse_rrule_params(rrule_values[0])
    freq_map = {"DAILY": "D", "WEEKLY": "W", "MONTHLY": "M", "YEARLY": "Y"}
    type_ = freq_map.get(params.get("FREQ", ""))
    if type_ is None:
        return None

    if UNSUPPORTED_RRULE_KEYS & params.keys():
        return None

    interval = int(params.get("INTERVAL", "1"))

    byday = params.get("BYDAY")
    days_bits = None
    if byday:
        if type_ != "W":
            return None  # e.g. "2nd Monday of the month" has no equivalent
        codes = byday.split(",")
        bits = ["0"] * 7
        for code in codes:
            if code not in DAY_CODE_TO_BIT_INDEX:
                return None  # ordinal-prefixed code like "2MO"/"-1FR"
            bits[DAY_CODE_TO_BIT_INDEX[code]] = "1"
        days_bits = "".join(bits)
    elif type_ == "W":
        # No BYDAY means "repeat on DTSTART's own weekday" — resolved in the
        # calendar's own timezone. This used to call fromtimestamp() with no
        # tz at all, which resolves in the timezone of whichever machine
        # happens to run the import, so an event starting near midnight got a
        # different weekday depending on where the script was run.
        weekday = datetime.fromtimestamp(event_start_epoch, tz=cal_tz).weekday()
        bits = ["0"] * 7
        bits[weekday] = "1"
        days_bits = "".join(bits)

    count = params.get("COUNT")
    until = params.get("UNTIL")
    if count and until:
        return None  # invalid per RFC5545, be defensive
    if count:
        end_type, count_val, until_val = "C", int(count), None
    elif until:
        end_type, count_val, until_val = "U", None, ics_value_to_epoch(until, None, cal_tz)
    else:
        end_type, count_val, until_val = "N", None, None

    fields = {
        "type": type_,
        "interval": interval,
        "days": days_bits,
        "endType": end_type,
        "count": count_val,
        "until": until_val,
    }
    exception_epochs = [
        to_exclusion_epoch(ics_value_to_epoch(v, tz, cal_tz), cal_tz)
        for v, tz in exdate_entries
    ]
    return fields, exception_epochs


def extract_reminder(item: dict) -> str | None:
    overrides = item.get("reminders", {}).get("overrides")
    if overrides:
        return f"{overrides[0]['minutes']}m"
    return None


# ── Import ────────────────────────────────────────────────────────────────────


def truncate_description(text: str | None) -> str | None:
    """Fit a Google description inside Self Calendar's own limit."""
    if text is None or len(text) <= MAX_DESCRIPTION_CHARS:
        return text
    return text[: MAX_DESCRIPTION_CHARS - 1] + "\u2026"


def build_event_payload(
    calendar_id: str, item: dict, category_id: str, date_start: int, date_end: int
) -> ObjEventSchemaCreate:
    return ObjEventSchemaCreate(
        calendar_id=calendar_id,
        title=(item.get("summary") or "(No title)")[:255],
        description=truncate_description(item.get("description")),
        date_start=date_start,
        date_end=date_end,
        category_id=category_id,
        address=item.get("location") or None,
        reminder=extract_reminder(item),
    )


def expand_via_instances(
    service,
    event_id: str,
    calendar_id: str,
    ensure_category,
    session: Session,
    cal_tz: ZoneInfo | timezone,
) -> int:
    count = 0
    page_token = None
    now = datetime.now(tz=timezone.utc)
    time_min = now.replace(year=now.year - EXPANSION_WINDOW_YEARS_BACK)
    time_max = now.replace(year=now.year + EXPANSION_WINDOW_YEARS_FORWARD)
    while True:
        resp = (
            service.events()
            .instances(
                calendarId="primary",
                eventId=event_id,
                maxResults=2500,
                pageToken=page_token,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
            )
            .execute(num_retries=5)
        )
        for inst in resp.get("items", []):
            if inst.get("status") == "cancelled":
                continue
            start, end = inst.get("start"), inst.get("end")
            if start is None or end is None:
                continue
            category_id = ensure_category(inst.get("colorId"))
            obj_event_service.create_event(
                build_event_payload(
                    calendar_id,
                    inst,
                    category_id,
                    parse_google_datetime(start, cal_tz),
                    parse_google_datetime(end, cal_tz),
                ),
                session,
            )
            count += 1
            if count >= MAX_EXPANDED_INSTANCES:
                print(
                    f"  Warning: event {event_id} exceeded "
                    f"{MAX_EXPANDED_INSTANCES} instances, truncating."
                )
                return count
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return count


def fetch_all_items(service) -> list[dict]:
    items = []
    page_token = None
    while True:
        resp = (
            service.events()
            .list(
                calendarId="primary",
                singleEvents=False,
                showDeleted=False,
                maxResults=2500,
                pageToken=page_token,
            )
            .execute(num_retries=5)
        )
        items.extend(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def run_import(
    service,
    session: Session,
    db_calendar,
    default_color: str,
    color_palette: dict,
    cal_tz: ZoneInfo | timezone,
) -> dict:
    category_cache: dict[str, str] = {}

    def ensure_category(color_id: str | None) -> str:
        key = color_id or "default"
        if key in category_cache:
            return category_cache[key]
        if color_id and color_id in color_palette:
            hexcolor = color_palette[color_id]["background"]
            title = GOOGLE_EVENT_COLOR_NAMES.get(color_id, f"Color {color_id}")
        else:
            hexcolor = default_color
            title = "Default"
        db_category = obj_category_service.create_category(
            ObjCategorySchemaCreate(
                calendar_id=db_calendar.id, title=title, color=hexcolor
            ),
            session,
        )
        category_cache[key] = db_category.id
        return db_category.id

    all_items = fetch_all_items(service)
    print(f"Fetched {len(all_items)} raw event resources from Google.")

    masters = [
        it
        for it in all_items
        if "recurringEventId" not in it and it.get("status") != "cancelled"
    ]
    overrides = [it for it in all_items if "recurringEventId" in it]

    # Google event id -> 'mapped' (has a Self Calendar recurrence row) or
    # 'expanded' (already fully materialized as individual events).
    master_kind: dict[str, str] = {}
    master_db_id: dict[str, str] = {}

    stats = {
        "plain": 0,
        "recurring_mapped": 0,
        "recurring_expanded_series": 0,
        "expanded_instances": 0,
        "overrides_modified": 0,
        "overrides_cancelled": 0,
        "skipped": 0,
    }

    for item in masters:
        start, end = item.get("start"), item.get("end")
        if start is None or end is None:
            stats["skipped"] += 1
            continue

        date_start = parse_google_datetime(start, cal_tz)
        date_end = parse_google_datetime(end, cal_tz)
        category_id = ensure_category(item.get("colorId"))

        if "recurrence" in item:
            analysis = analyze_recurrence(item["recurrence"], date_start, cal_tz)
            if analysis is not None:
                fields, exception_epochs = analysis
                payload = build_event_payload(
                    db_calendar.id, item, category_id, date_start, date_end
                )
                payload.obj_recurence = ObjEventRecurenceSchemaCreate(**fields)
                db_event = obj_event_service.create_event(payload, session)
                for exc_epoch in exception_epochs:
                    obj_event_service.add_exception_event_recurence(
                        db_event.id, exc_epoch, session
                    )
                master_kind[item["id"]] = "mapped"
                master_db_id[item["id"]] = db_event.id
                stats["recurring_mapped"] += 1
            else:
                master_kind[item["id"]] = "expanded"
                stats["recurring_expanded_series"] += 1
                stats["expanded_instances"] += expand_via_instances(
                    service, item["id"], db_calendar.id, ensure_category, session,
                    cal_tz,
                )
        else:
            obj_event_service.create_event(
                build_event_payload(
                    db_calendar.id, item, category_id, date_start, date_end
                ),
                session,
            )
            stats["plain"] += 1

    for item in overrides:
        kind = master_kind.get(item["recurringEventId"])
        if kind != "mapped":
            # Master was expansion-based (instances() already reflects this
            # override) or wasn't imported at all — nothing more to do.
            continue

        original_start = item.get("originalStartTime")
        if original_start is None:
            continue
        db_event_id = master_db_id[item["recurringEventId"]]
        obj_event_service.add_exception_event_recurence(
            db_event_id,
            to_exclusion_epoch(parse_google_datetime(original_start, cal_tz), cal_tz),
            session,
        )

        if item.get("status") == "cancelled":
            stats["overrides_cancelled"] += 1
            continue

        start, end = item.get("start"), item.get("end")
        if start is None or end is None:
            continue
        category_id = ensure_category(item.get("colorId"))
        obj_event_service.create_event(
            build_event_payload(
                db_calendar.id,
                item,
                category_id,
                parse_google_datetime(start, cal_tz),
                parse_google_datetime(end, cal_tz),
            ),
            session,
        )
        stats["overrides_modified"] += 1

    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a Google account's primary calendar into Self Calendar."
    )
    parser.add_argument(
        "--username", required=True,
        help="Existing Self Calendar username to own the imported calendar.",
    )
    parser.add_argument(
        "--credentials", default=str(Path(__file__).parent / "credentials.json"),
        help="Path to the OAuth client secrets JSON from Google Cloud Console.",
    )
    parser.add_argument(
        "--token", default=str(Path(__file__).parent / "token.json"),
        help="Path where the OAuth token is cached between runs.",
    )
    parser.add_argument(
        "--calendar-title", default=None,
        help="Override the created calendar's title (default: 'Google <account email>').",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip the confirmation prompt.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    creds = get_credentials(Path(args.credentials), Path(args.token))
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    primary = service.calendars().get(calendarId="primary").execute(num_retries=5)
    account_name = primary["id"]  # for the primary calendar this is the account email
    cal_tz = resolve_timezone(primary.get("timeZone"))
    cal_list_entry = (
        service.calendarList().get(calendarId="primary").execute(num_retries=5)
    )
    default_color = cal_list_entry.get("backgroundColor", "#4285F4")
    color_palette = service.colors().get().execute(num_retries=5)["event"]

    calendar_title = args.calendar_title or f"Google {account_name}"

    print(
        f"About to import events from the primary Google Calendar of "
        f"'{account_name}' into a NEW calendar '{calendar_title}', "
        f"owned by Self Calendar user '{args.username}'."
    )
    print(f"All-day dates and exclusions are anchored to {cal_tz}.")
    print("This does not deduplicate — re-running creates another calendar.")
    if not args.yes and input("Continue? [y/N] ").strip().lower() != "y":
        print("Aborted.")
        return

    create_db_and_tables()
    with Session(db_engine) as session:
        db_user = session.exec(
            select(ObjUserModel).where(ObjUserModel.username == args.username)
        ).first()
        if not db_user:
            print(f"No such Self Calendar user: {args.username}")
            sys.exit(1)
        set_logged_user_context(db_user)

        db_calendar = obj_calendar_service.create_calendar(
            ObjCalendarSchemaCreate(
                title=calendar_title,
                description=f"Imported from Google Calendar ({account_name})",
                color=default_color,
            ),
            session,
        )
        print(f"Created calendar {db_calendar.id!r} '{db_calendar.title}'")

        stats = run_import(
            service, session, db_calendar, default_color, color_palette, cal_tz
        )

    print("Import complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
