"""
Security-hardening regression tests.

Each test pins one finding from the 2026-11 security pass. All of them were
reproduced against the previous code first — the brute-force bypass as a
missing 429, the others as HTTP 500s or silently-accepted input.
"""

import jwt
import pytest
from pydantic import ValidationError
from sqlmodel import Session

import app.app as app_module
from app.common.config import Settings, settings
from app.common.db_connection import db_engine
from app.common.middleware import rate_limit_middleware
from app.models.obj_event_model import ObjEventModel
from tests.conftest import auth_headers, register_and_login

PASSWORD = "supersecret123"

# 2026-01-05 (a Monday) 09:00 UTC — any ordinary date inside the bounds.
T0 = 1767603600
DAY = 86400


def _make_calendar(client, token, title="Cal"):
    r = client.post(
        "/calendar/",
        json={"title": title, "color": "#ffffff"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _make_event(client, token, calendar_id, **overrides):
    body = {
        "calendar_id": calendar_id,
        "title": "Event",
        "date_start": T0,
        "date_end": T0 + 3600,
        **overrides,
    }
    return client.post("/event/", json=body, headers=auth_headers(token))


def _login(client, username, password=PASSWORD):
    return client.post(
        "/auth/login", json={"username": username, "password": password}
    )


# ── Rate limiting ────────────────────────────────────────────────────────────


def test_successful_login_does_not_reset_failure_count(client):
    """A success used to wipe the IP's failures, so an attacker with any
    account could log into it every few guesses and brute-force someone
    else's password from one IP indefinitely."""
    register_and_login(client, "attacker")
    register_and_login(client, "victim")
    rate_limit_middleware._store.clear()

    limit = settings.RATE_LIMIT_MAX_FAILURES
    for i in range(limit - 1):
        assert _login(client, "victim", f"wrong-guess-{i}").status_code == 401
    # The attacker's own, valid login in between...
    assert _login(client, "attacker").status_code == 200
    # ...no longer buys more guesses: this failure reaches the limit.
    assert _login(client, "victim", "wrong-guess-last").status_code == 401

    blocked = _login(client, "victim", PASSWORD)
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["error_code"] == "RATE_LIMITED"


def test_failures_outside_the_window_are_forgotten(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_MAX_FAILURES", 3)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 100)
    ip = "198.51.100.7"

    assert rate_limit_middleware._record_failure(ip, 1000.0) is False
    assert rate_limit_middleware._record_failure(ip, 1050.0) is False
    # 1000 has aged out of the window by now, so this is only the 2nd.
    assert rate_limit_middleware._record_failure(ip, 1101.0) is False
    # 1050, 1101 and this one are all within 100s of each other.
    assert rate_limit_middleware._record_failure(ip, 1102.0) is True


def test_change_password_is_rate_limited(client):
    """Guessing the current password with a stolen access token."""
    token = register_and_login(client, "alice")
    rate_limit_middleware._store.clear()

    for i in range(settings.RATE_LIMIT_MAX_FAILURES):
        r = client.patch(
            "/user/password",
            json={"old_password": f"guess-{i}", "new_password": "x" * 20},
            headers=auth_headers(token),
        )
        assert r.status_code == 401

    r = client.patch(
        "/user/password",
        json={"old_password": PASSWORD, "new_password": "x" * 20},
        headers=auth_headers(token),
    )
    assert r.status_code == 429


# ── bcrypt's 72-byte limit ──────────────────────────────────────────────────


def test_register_rejects_password_over_72_bytes_not_chars(client):
    """40 accented characters pass max_length=72 but are 80 bytes."""
    r = client.post(
        "/auth/register", json={"username": "mb", "password": "é" * 40}
    )
    assert r.status_code == 422


def test_login_with_overlong_password_is_a_plain_401(client):
    register_and_login(client, "alice")
    assert _login(client, "alice", "x" * 100).status_code == 401
    assert _login(client, "nobody", "x" * 100).status_code == 401


def test_change_password_with_overlong_old_password_is_a_plain_401(client):
    token = register_and_login(client, "alice")
    r = client.patch(
        "/user/password",
        json={"old_password": "x" * 100, "new_password": "y" * 20},
        headers=auth_headers(token),
    )
    assert r.status_code == 401


# ── JWT / configuration ──────────────────────────────────────────────────────


def test_token_without_exp_is_rejected(client):
    token = register_and_login(client, "alice")
    me = client.get("/auth/me", headers=auth_headers(token)).json()

    forged = jwt.encode(
        {"userId": me["id"], "tokenVersion": 0, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    assert client.get("/auth/me", headers=auth_headers(forged)).status_code == 401


def test_short_secret_key_refuses_to_start(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "too-short-but-not-placeholder")
    with pytest.raises(RuntimeError, match="too short"):
        app_module._require_real_secret_key()


def test_only_hmac_algorithms_are_accepted():
    with pytest.raises(ValidationError):
        Settings(ALGORITHM="none")
    with pytest.raises(ValidationError):
        Settings(ALGORITHM="RS256")


def test_cors_does_not_allow_credentials():
    """Auth is a bearer header, never a cookie — credentials mode is unused."""
    cors = [m for m in app_module.app.user_middleware if m.cls.__name__ == "CORSMiddleware"]
    assert len(cors) == 1
    assert cors[0].kwargs["allow_credentials"] is False


# ── Event input validation ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "overrides",
    [
        {"address": "a" * 256},
        {"reminder": "r" * 256},
        {"color": "red;x:y"},
        {"date_end": 10**18},
        {"date_start": -(10**18)},
        {
            "obj_recurence": {
                "type": "D", "interval": 1, "endType": "U", "until": 10**18,
            }
        },
    ],
)
def test_event_create_rejects_out_of_range_input(client, overrides):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    assert _make_event(client, token, calendar_id, **overrides).status_code == 422


@pytest.mark.parametrize(
    "patch",
    [{"address": "a" * 256}, {"color": "0;all:0"}, {"date_end": 10**18}],
)
def test_event_patch_rejects_out_of_range_input(client, patch):
    """PATCH used setattr() straight onto the row, bypassing the model's own
    max_length entirely."""
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    event_id = _make_event(client, token, calendar_id).json()["id"]
    r = client.patch(f"/event/{event_id}", json=patch, headers=auth_headers(token))
    assert r.status_code == 422


def test_event_color_accepts_hex_and_null(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    r = _make_event(client, token, calendar_id, color="#a1B2c3")
    assert r.status_code == 200 and r.json()["color"] == "#a1B2c3"
    event_id = r.json()["id"]
    r = client.patch(
        f"/event/{event_id}", json={"color": None}, headers=auth_headers(token)
    )
    assert r.status_code == 200 and r.json()["color"] is None


def test_exception_date_is_bounded(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    event_id = _make_event(
        client, token, calendar_id,
        obj_recurence={"type": "D", "interval": 1, "endType": "N"},
    ).json()["id"]
    r = client.delete(f"/event/{event_id}/{10**18}", headers=auth_headers(token))
    assert r.status_code == 422


# ── Recurrence expansion robustness ──────────────────────────────────────────


def test_expand_without_to_date_works(client):
    """to_date defaults to sys.maxsize, which datetime cannot represent."""
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    event_id = _make_event(client, token, calendar_id).json()["id"]

    r = client.get(
        "/event/range",
        params={"calendar_ids": calendar_id, "expand": "true"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    assert [o["event"]["id"] for o in r.json()] == [event_id]


def test_one_unrepresentable_event_does_not_break_the_calendar(client):
    """A row with an out-of-range date (stored before validation existed)
    used to 500 every expanded read of its calendar — for every member."""
    owner = register_and_login(client, "owner")
    calendar_id = _make_calendar(client, owner)
    good_id = _make_event(client, owner, calendar_id).json()["id"]

    with Session(db_engine) as session:
        session.add(
            ObjEventModel(
                calendar_id=calendar_id, title="poison",
                date_start=T0, date_end=10**18, address=None, reminder=None,
            )
        )
        session.commit()

    r = client.get(
        "/event/range",
        params={
            "calendar_ids": calendar_id, "expand": "true",
            "from_date": T0 - DAY, "to_date": T0 + DAY,
        },
        headers=auth_headers(owner),
    )
    assert r.status_code == 200, r.text
    assert [o["event"]["id"] for o in r.json()] == [good_id]


def test_huge_count_times_interval_does_not_overflow(client):
    """count and interval are each <= 1000; a yearly rule's product of the
    two is a million years, past datetime's year 9999."""
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    r = _make_event(
        client, token, calendar_id,
        obj_recurence={"type": "Y", "interval": 1000, "endType": "C", "count": 1000},
    )
    assert r.status_code == 200, r.text
    assert r.json()["obj_recurence"]["estimated_end_date"] is None


# ── Server-owned recurrence fields ───────────────────────────────────────────


def test_client_cannot_choose_recurrence_id(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    event_id = _make_event(
        client, token, calendar_id,
        obj_recurence={"type": "D", "interval": 1, "endType": "N"},
    ).json()["id"]

    r = client.patch(
        f"/event/{event_id}",
        json={
            "obj_recurence": {
                "id": "attacker-chosen-id", "type": "D", "interval": 2, "endType": "N",
            }
        },
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["obj_recurence"]["id"] != "attacker-chosen-id"


def test_client_cannot_attach_exception_rows_on_create(client):
    """Including another calendar's exception (by id) used to make the
    server try to insert/attach it."""
    victim = register_and_login(client, "victim")
    attacker = register_and_login(client, "attacker")
    victim_cal = _make_calendar(client, victim)
    attacker_cal = _make_calendar(client, attacker)

    recurring = {"type": "D", "interval": 1, "endType": "N"}
    victim_event = _make_event(client, victim, victim_cal, obj_recurence=recurring).json()
    client.delete(f"/event/{victim_event['id']}/{T0 + DAY}", headers=auth_headers(victim))
    victim_event = client.get(
        f"/event/{victim_event['id']}", headers=auth_headers(victim)
    ).json()
    stolen = victim_event["obj_recurence"]["obj_exceptions"][0]

    r = _make_event(
        client, attacker, attacker_cal,
        obj_recurence={**recurring, "obj_exceptions": [stolen]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["obj_recurence"]["obj_exceptions"] == []

    after = client.get(f"/event/{victim_event['id']}", headers=auth_headers(victim)).json()
    assert after["obj_recurence"]["obj_exceptions"] == [stolen]


# ── PATCH with null on NOT NULL columns ──────────────────────────────────────


def test_category_patch_with_null_calendar_id_and_title_is_ignored(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    category = client.post(
        "/category/",
        json={"calendar_id": calendar_id, "title": "Work", "color": "#000000"},
        headers=auth_headers(token),
    ).json()

    r = client.patch(
        f"/category/{category['id']}",
        json={"calendar_id": None, "title": None, "color": "#ffffff"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["calendar_id"] == calendar_id
    assert r.json()["title"] == "Work"
    assert r.json()["color"] == "#ffffff"


def test_calendar_patch_with_null_title_is_ignored(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token, title="Home")
    r = client.patch(
        f"/calendar/{calendar_id}", json={"title": None}, headers=auth_headers(token)
    )
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Home"
