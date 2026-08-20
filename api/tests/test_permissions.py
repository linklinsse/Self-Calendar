"""
Permission / authorization regression tests.

These pin the specific critical findings from self-calendar-code-review.md
that a static read-through missed and only an HTTP-level test would catch
— #1 (missing authz on get_lnk_user_calendar), #2 (privilege escalation via
the "first membership is free" trust inference), and the category
cross-calendar leak. If any of these regress, this file should fail loudly.
"""

import time
from datetime import datetime, timezone

import pytest

from tests.conftest import auth_headers, register_and_login


def _make_calendar(client, token, title="Cal"):
    r = client.post(
        "/calendar/",
        json={"title": title, "description": "d", "color": "#ffffff"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_create_calendar_grants_owner_atomically(client):
    token = register_and_login(client, "alice")
    calendar = _make_calendar(client, token)
    assert calendar["user_right"] == "O"


def test_cannot_seize_unowned_calendar_via_user_calendar_create(client):
    """Critical #2: a non-owner must not be able to POST /user_calendar/
    with someone else's calendar_id and right=O."""
    alice = register_and_login(client, "alice")
    bob = register_and_login(client, "bob")
    calendar = _make_calendar(client, alice)

    r = client.post(
        "/user_calendar/",
        json={"username": "bob", "calendar_id": calendar["id"], "right": "O"},
        headers=auth_headers(bob),
    )
    assert r.status_code in (403, 404)


def test_get_membership_requires_calendar_access(client):
    """Critical #1: GET /user_calendar/{id} must check the caller has
    access to the *linked calendar*, not just that the row exists."""
    alice = register_and_login(client, "alice")
    bob = register_and_login(client, "bob")
    bob_calendar = _make_calendar(client, bob, "Bob's calendar")

    r = client.get(f"/user_calendar/all/{bob_calendar['id']}", headers=auth_headers(bob))
    bob_own_membership_id = r.json()[0]["id"]

    r = client.get(f"/user_calendar/{bob_own_membership_id}", headers=auth_headers(alice))
    assert r.status_code == 404


def test_shared_calendar_membership_is_visible_to_members(client):
    alice = register_and_login(client, "alice")
    register_and_login(client, "bob")  # just needs to exist
    calendar = _make_calendar(client, alice)

    r = client.post(
        "/user_calendar/",
        json={"username": "bob", "calendar_id": calendar["id"], "right": "R"},
        headers=auth_headers(alice),
    )
    assert r.status_code == 200, r.text
    lnk_id = r.json()["id"]

    r = client.get(f"/user_calendar/{lnk_id}", headers=auth_headers(alice))
    assert r.status_code == 200


def test_category_cannot_be_attached_across_calendars(client):
    token = register_and_login(client, "carol")
    cal_a = _make_calendar(client, token, "A")
    cal_b = _make_calendar(client, token, "B")

    r = client.post(
        "/category/",
        json={"calendar_id": cal_b["id"], "title": "B-only", "color": "#123456"},
        headers=auth_headers(token),
    )
    cat_b = r.json()["id"]

    now = int(time.time())
    r = client.post(
        "/event/",
        json={
            "calendar_id": cal_a["id"],
            "title": "Cross-cal category",
            "date_start": now,
            "date_end": now + 3600,
            "category_id": cat_b,
        },
        headers=auth_headers(token),
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error_code"] == "CATEGORY_NOT_FOUND"


def test_registration_disabled_is_reported_honestly(client, monkeypatch):
    """USER_CREATION=False previously reused INVALID_CREDENTIALS, so a server
    with registration closed told visitors their username and password were
    wrong. It must say what is actually happening, and /auth/config must
    advertise it so the client can hide the Register tab."""
    from app.common.config import settings

    r = client.get("/auth/config")
    assert r.status_code == 200
    assert r.json()["user_creation"] is True

    monkeypatch.setattr(settings, "USER_CREATION", False)

    r = client.get("/auth/config")
    assert r.json()["user_creation"] is False

    r = client.post(
        "/auth/register", json={"username": "nope", "password": "supersecret123"}
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error_code"] == "REGISTRATION_DISABLED"


def test_deleting_a_category_clears_it_from_its_events(client):
    """Deleting a category must not leave events pointing at a row that no
    longer exists — such an event renders uncategorised *and* can no longer
    be edited through the UI, because any PATCH echoing the stale
    category_id back is rejected by _validate_category_in_calendar."""
    token = register_and_login(client, "frank")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)
    now = int(time.time())

    r = client.post(
        "/category/",
        json={"calendar_id": calendar["id"], "title": "Work", "color": "#123456"},
        headers=h,
    )
    category_id = r.json()["id"]

    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"],
            "title": "Categorised",
            "date_start": now,
            "date_end": now + 3600,
            "category_id": category_id,
        },
        headers=h,
    )
    event_id = r.json()["id"]

    r = client.delete(f"/category/{category_id}", headers=h)
    assert r.status_code == 204, r.text

    r = client.get(f"/event/{event_id}", headers=h)
    assert r.status_code == 200
    assert r.json()["category_id"] is None

    # And the event is still editable.
    r = client.patch(f"/event/{event_id}", json={"title": "Renamed"}, headers=h)
    assert r.status_code == 200, r.text


def test_recurence_id_is_not_client_settable(client):
    """A user must not be able to bind their own event to a recurrence row
    belonging to a calendar they have no access to.

    Before the fix, `recurence_id` was a writable field on both the create
    and edit schemas, so Bob could point his own event at Alice's recurrence,
    read her rule back via GET, and then destroy it (plus every exception on
    it) simply by deleting his own event — delete_event cascades into the
    attached recurrence.
    """
    alice = register_and_login(client, "alice")
    bob = register_and_login(client, "bob")
    now = int(time.time())

    cal_a = _make_calendar(client, alice, "Alice private")
    r = client.post(
        "/event/",
        json={
            "calendar_id": cal_a["id"],
            "title": "Alice standup",
            "date_start": now,
            "date_end": now + 3600,
            "obj_recurence": {
                "type": "W", "interval": 3, "endType": "C", "count": 42,
            },
        },
        headers=auth_headers(alice),
    )
    assert r.status_code == 200, r.text
    alice_event_id = r.json()["id"]
    alice_recurence_id = r.json()["recurence_id"]
    assert alice_recurence_id is not None

    cal_b = _make_calendar(client, bob, "Bob")
    r = client.post(
        "/event/",
        json={
            "calendar_id": cal_b["id"],
            "title": "Bob event",
            "date_start": now,
            "date_end": now + 3600,
            "recurence_id": alice_recurence_id,
        },
        headers=auth_headers(bob),
    )
    assert r.status_code == 200, r.text
    bob_event_id = r.json()["id"]
    # The field is ignored, not honoured.
    assert r.json()["recurence_id"] is None
    assert r.json()["obj_recurence"] is None

    r = client.patch(
        f"/event/{bob_event_id}",
        json={"recurence_id": alice_recurence_id},
        headers=auth_headers(bob),
    )
    assert r.status_code == 200, r.text
    assert r.json()["recurence_id"] is None

    # Bob deleting his own event must not touch Alice's recurrence.
    r = client.delete(f"/event/{bob_event_id}", headers=auth_headers(bob))
    assert r.status_code == 200, r.text

    r = client.get(f"/event/{alice_event_id}", headers=auth_headers(alice))
    assert r.status_code == 200
    assert r.json()["obj_recurence"] is not None
    assert r.json()["obj_recurence"]["count"] == 42


def test_disabled_account_is_rejected_at_login_and_for_existing_tokens(client):
    from app.common.db_connection import db_engine
    from sqlmodel import Session, select
    from app.models.obj_user_model import ObjUserModel

    token = register_and_login(client, "dave")

    with Session(db_engine) as session:
        user = session.exec(select(ObjUserModel).where(ObjUserModel.username == "dave")).first()
        user.disabled = True
        session.add(user)
        session.commit()

    r = client.post("/auth/login", json={"username": "dave", "password": "supersecret123"})
    assert r.status_code == 401

    r = client.get("/auth/me", headers=auth_headers(token))
    assert r.status_code == 401


def test_password_change_invalidates_existing_tokens(client):
    old_token = register_and_login(client, "erin")

    r = client.patch(
        "/user/password",
        json={"old_password": "supersecret123", "new_password": "newsupersecret456"},
        headers=auth_headers(old_token),
    )
    assert r.status_code == 200, r.text

    r = client.get("/auth/me", headers=auth_headers(old_token))
    assert r.status_code == 401

    r = client.post("/auth/login", json={"username": "erin", "password": "newsupersecret456"})
    assert r.status_code == 200


def test_container_refuses_to_start_on_a_non_persistent_db(monkeypatch):
    """The most-reported failure in this project: the database appears to
    reset on every `docker compose down && up`.

    It is never a Docker or SQLite bug — DB_URL defaults to
    `sqlite:///./dev.db`, which resolves inside the container's own writable
    layer rather than the mounted /work/db, so the file dies with the
    container. Previously silent; now a startup failure that names the cause.
    """
    from app.app import _require_persistent_db
    from app.common.config import settings

    monkeypatch.setenv("SELFCALENDAR_IN_CONTAINER", "1")

    monkeypatch.setattr(settings, "DB_URL", "sqlite:////work/dev.db")
    with pytest.raises(RuntimeError, match="destroyed on the next"):
        _require_persistent_db()

    # On the mount, it starts.
    monkeypatch.setattr(settings, "DB_URL", "sqlite:////work/db/prod.db")
    _require_persistent_db()

    # A real database server persists on its own terms.
    monkeypatch.setattr(settings, "DB_URL", "postgresql+psycopg2://u:p@host/db")
    _require_persistent_db()


def test_outside_a_container_any_db_path_is_fine(monkeypatch):
    """Outside Docker the same path is just a file on disk and survives, so
    the check must not fire — it would break every local dev run."""
    from app.app import _require_persistent_db
    from app.common.config import settings

    monkeypatch.delenv("SELFCALENDAR_IN_CONTAINER", raising=False)
    monkeypatch.setattr(settings, "DB_URL", "sqlite:///./dev.db")
    _require_persistent_db()


def test_refresh_token_flow(client):
    """The widget holds its own token and stops working when it expires —
    the user may not open the app for weeks. A refresh token lets it mint
    new access tokens on its own."""
    token = register_and_login(client, "grace")

    r = client.post("/auth/refresh-token", headers=auth_headers(token))
    assert r.status_code == 200, r.text
    refresh_token = r.json()["refresh_token"]

    r = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200, r.text
    new_access = r.json()
    assert isinstance(new_access, str)

    # The minted token works.
    r = client.get("/auth/me", headers=auth_headers(new_access))
    assert r.status_code == 200
    assert r.json()["username"] == "grace"


def test_refresh_token_is_not_usable_as_an_access_token(client):
    """Both are signed with the same secret, so without the type claim a
    30-day refresh token would authenticate the entire API — the exact thing
    short access-token lifetimes exist to prevent."""
    token = register_and_login(client, "heidi")
    refresh_token = client.post(
        "/auth/refresh-token", headers=auth_headers(token)
    ).json()["refresh_token"]

    r = client.get("/auth/me", headers=auth_headers(refresh_token))
    assert r.status_code == 401
    assert r.json()["detail"]["error_code"] == "INVALID_TOKEN"


def test_access_token_cannot_be_exchanged_for_a_new_one(client):
    """Otherwise an access token renews itself indefinitely and its short
    lifetime means nothing."""
    token = register_and_login(client, "ivan")
    r = client.post("/auth/refresh", json={"refresh_token": token})
    assert r.status_code == 401


def test_password_change_invalidates_refresh_tokens(client):
    """Refresh tokens are long-lived, so the password-change remedy has to
    reach them or a stolen one outlives the fix by a month."""
    token = register_and_login(client, "judy", password="original-pw-123")
    refresh_token = client.post(
        "/auth/refresh-token", headers=auth_headers(token)
    ).json()["refresh_token"]

    r = client.patch(
        "/user/password",
        json={"old_password": "original-pw-123", "new_password": "brand-new-pw-456"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text

    r = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401


def test_range_expand_returns_one_entry_per_occurrence(client):
    """?expand=true makes the server do recurrence expansion, so clients
    don't each reimplement it. The Android widget relies on this and expands
    nothing itself."""
    token = register_and_login(client, "karl")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)

    # Wed 2026-03-04 09:00 UTC, weekly on Wednesdays.
    start = int(datetime(2026, 3, 4, 9, 0, tzinfo=timezone.utc).timestamp())
    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"],
            "title": "Standup",
            "date_start": start,
            "date_end": start + 3600,
            "obj_recurence": {
                "type": "W", "interval": 1, "days": "0010000", "endType": "N",
            },
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    event_id = r.json()["id"]

    range_start = int(datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp())
    range_end = int(datetime(2026, 3, 31, 23, 59, tzinfo=timezone.utc).timestamp())

    # Unexpanded: one row, rule attached.
    r = client.get(
        f"/event/range?calendar_ids={calendar['id']}"
        f"&from_date={range_start}&to_date={range_end}",
        headers=h,
    )
    assert len(r.json()) == 1
    assert r.json()[0]["obj_recurence"] is not None

    # Expanded: every Wednesday in March 2026 — 4, 11, 18, 25.
    r = client.get(
        f"/event/range?calendar_ids={calendar['id']}"
        f"&from_date={range_start}&to_date={range_end}"
        f"&expand=true&timezone=UTC",
        headers=h,
    )
    assert r.status_code == 200, r.text
    occurrences = r.json()
    assert len(occurrences) == 4
    assert all(o["event"]["id"] == event_id for o in occurrences)
    days = [
        datetime.fromtimestamp(o["date_start"], tz=timezone.utc).day
        for o in occurrences
    ]
    assert days == [4, 11, 18, 25]
    # The occurrence keeps the original event's duration.
    assert occurrences[0]["date_end"] - occurrences[0]["date_start"] == 3600


def test_range_expand_omits_excluded_occurrences(client):
    """Exclusions are applied server-side, so a client cannot forget to."""
    token = register_and_login(client, "lena")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)

    start = int(datetime(2026, 3, 4, 9, 0, tzinfo=timezone.utc).timestamp())
    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "Standup",
            "date_start": start, "date_end": start + 3600,
            "obj_recurence": {
                "type": "W", "interval": 1, "days": "0010000", "endType": "N",
            },
        },
        headers=h,
    )
    event_id = r.json()["id"]

    # Skip the 11th.
    skipped = int(datetime(2026, 3, 11, tzinfo=timezone.utc).timestamp())
    assert client.delete(f"/event/{event_id}/{skipped}", headers=h).status_code == 200

    range_start = int(datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp())
    range_end = int(datetime(2026, 3, 31, 23, 59, tzinfo=timezone.utc).timestamp())
    r = client.get(
        f"/event/range?calendar_ids={calendar['id']}"
        f"&from_date={range_start}&to_date={range_end}&expand=true&timezone=UTC",
        headers=h,
    )
    days = [
        datetime.fromtimestamp(o["date_start"], tz=timezone.utc).day
        for o in r.json()
    ]
    assert days == [4, 18, 25]


def test_range_expand_passes_through_non_recurring_events(client):
    token = register_and_login(client, "mona")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)

    start = int(datetime(2026, 3, 10, 14, 0, tzinfo=timezone.utc).timestamp())
    client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "One-off",
            "date_start": start, "date_end": start + 1800,
        },
        headers=h,
    )

    range_start = int(datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp())
    range_end = int(datetime(2026, 3, 31, 23, 59, tzinfo=timezone.utc).timestamp())
    r = client.get(
        f"/event/range?calendar_ids={calendar['id']}"
        f"&from_date={range_start}&to_date={range_end}&expand=true&timezone=UTC",
        headers=h,
    )
    assert len(r.json()) == 1
    assert r.json()[0]["date_start"] == start


def test_duplicate_membership_is_blocked_by_the_database(client):
    """create_lnk_user_calendar checks for an existing membership before
    inserting, which is a check-then-act race: two concurrent requests both
    see nothing and both insert, leaving the user with two different rights
    on one calendar and verify_user_right_calendar picking whichever comes
    back first. The unique constraint closes it regardless of code path."""
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import Session

    from app.common.db_connection import db_engine
    from app.models.lnk_user_calendar_model import LnkUserCalendarModel

    owner = register_and_login(client, "nate")
    calendar = _make_calendar(client, owner)

    r = client.get("/auth/me", headers=auth_headers(owner))
    user_id = r.json()["id"]

    # Bypass the service entirely — the point is that the database refuses.
    with Session(db_engine) as session:
        session.add(
            LnkUserCalendarModel(
                user_id=user_id, calendar_id=calendar["id"], right="R"
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_two_events_cannot_share_a_recurrence(client):
    """delete_event cascades into the attached recurrence, so a shared one
    means deleting either event destroys the other's rule. This was remotely
    reachable while recurence_id was client-settable; the constraint makes it
    unrepresentable rather than merely unreachable."""
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import Session, select

    from app.common.db_connection import db_engine
    from app.models.obj_event_model import ObjEventModel

    token = register_and_login(client, "olive")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)
    now = int(time.time())

    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "Recurring",
            "date_start": now, "date_end": now + 3600,
            "obj_recurence": {"type": "D", "interval": 1, "endType": "N"},
        },
        headers=h,
    )
    recurrence_id = r.json()["recurence_id"]

    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "Other",
            "date_start": now, "date_end": now + 3600,
        },
        headers=h,
    )
    other_id = r.json()["id"]

    with Session(db_engine) as session:
        other = session.exec(
            select(ObjEventModel).where(ObjEventModel.id == other_id)
        ).one()
        other.recurence_id = recurrence_id
        session.add(other)
        with pytest.raises(IntegrityError):
            session.commit()


def test_event_cannot_reference_a_nonexistent_category(client):
    """The service clears category_id when a category is deleted, but that is
    one call site. The foreign key holds for every write path."""
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import Session, select

    from app.common.db_connection import db_engine
    from app.models.obj_event_model import ObjEventModel

    token = register_and_login(client, "pete")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)
    now = int(time.time())

    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "E",
            "date_start": now, "date_end": now + 60,
        },
        headers=h,
    )
    event_id = r.json()["id"]

    with Session(db_engine) as session:
        event = session.exec(
            select(ObjEventModel).where(ObjEventModel.id == event_id)
        ).one()
        event.category_id = "does-not-exist"
        session.add(event)
        with pytest.raises(IntegrityError):
            session.commit()


def test_event_color_override_is_optional_and_round_trips(client):
    """Per-event colour. Null means "inherit the category's colour", which
    has to stay distinguishable from a user deliberately picking that same
    colour — otherwise there is no way back to inheriting."""
    token = register_and_login(client, "quinn")
    h = auth_headers(token)
    calendar = _make_calendar(client, token)
    now = int(time.time())

    r = client.post(
        "/category/",
        json={"calendar_id": calendar["id"], "title": "Work", "color": "#123456"},
        headers=h,
    )
    category_id = r.json()["id"]

    # No colour given -> null, i.e. inherit.
    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "Inherits",
            "date_start": now, "date_end": now + 60,
            "category_id": category_id,
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    inheriting_id = r.json()["id"]
    assert r.json()["color"] is None

    # Explicit override survives the round trip.
    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"], "title": "Override",
            "date_start": now, "date_end": now + 60,
            "category_id": category_id, "color": "#ff8800",
        },
        headers=h,
    )
    assert r.json()["color"] == "#ff8800"
    override_id = r.json()["id"]

    # And can be set, then cleared back to inheriting.
    r = client.patch(f"/event/{inheriting_id}", json={"color": "#00ff00"}, headers=h)
    assert r.json()["color"] == "#00ff00"

    r = client.patch(f"/event/{override_id}", json={"color": None}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["color"] is None, (
        "setting color to null must clear the override, not be ignored — "
        "otherwise an event can never go back to following its category"
    )
