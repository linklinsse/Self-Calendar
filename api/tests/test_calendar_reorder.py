"""
Calendar reordering (TODO: "we should be able to reorder calendar").

Ranking lives on lnk_user_calendar (per-user), not obj_calendar, so these
tests pin two things a global-rank design would get wrong: reordering one
user's list must not touch another user's copy of a shared calendar's
position, and GET /calendar/ must come back in that per-user order.
"""

from tests.conftest import auth_headers, register_and_login


def _make_calendar(client, token, title="Cal"):
    r = client.post(
        "/calendar/",
        json={"title": title, "description": "d", "color": "#ffffff"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    return r.json()


def _titles(client, token):
    r = client.get("/calendar/", headers=auth_headers(token))
    assert r.status_code == 200, r.text
    return [c["title"] for c in r.json()]


def test_new_calendars_are_returned_in_creation_order(client):
    token = register_and_login(client, "cal_order_alice")
    _make_calendar(client, token, "First")
    _make_calendar(client, token, "Second")
    _make_calendar(client, token, "Third")

    assert _titles(client, token) == ["First", "Second", "Third"]


def test_reorder_persists_and_is_reflected_in_get_all(client):
    token = register_and_login(client, "cal_order_bob")
    a = _make_calendar(client, token, "A")
    b = _make_calendar(client, token, "B")
    c = _make_calendar(client, token, "C")

    r = client.patch(
        "/calendar/reorder",
        json={"calendar_ids": [c["id"], a["id"], b["id"]]},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text

    assert _titles(client, token) == ["C", "A", "B"]


def test_reorder_is_per_user_not_global(client):
    """Two users sharing a calendar must be able to keep it in a different
    position in their own list — ranking is per-membership, not a property
    of obj_calendar itself."""
    alice = register_and_login(client, "cal_order_carol")
    bob = register_and_login(client, "cal_order_dave")

    shared = _make_calendar(client, alice, "Shared")
    alice_only = _make_calendar(client, alice, "Alice-only")

    client.post(
        "/user_calendar/",
        json={"username": "cal_order_dave", "calendar_id": shared["id"], "right": "R"},
        headers=auth_headers(alice),
    )
    bob_only = _make_calendar(client, bob, "Bob-only")

    # Alice: Shared first. Bob: Shared last.
    r = client.patch(
        "/calendar/reorder",
        json={"calendar_ids": [shared["id"], alice_only["id"]]},
        headers=auth_headers(alice),
    )
    assert r.status_code == 200, r.text

    r = client.patch(
        "/calendar/reorder",
        json={"calendar_ids": [bob_only["id"], shared["id"]]},
        headers=auth_headers(bob),
    )
    assert r.status_code == 200, r.text

    assert _titles(client, alice) == ["Shared", "Alice-only"]
    assert _titles(client, bob) == ["Bob-only", "Shared"]


def test_reorder_rejects_a_partial_list(client):
    """Silently accepting fewer ids than the caller owns would leave the
    calendars left out with an unspecified rank relative to the reordered
    ones — reject instead of guessing."""
    token = register_and_login(client, "cal_order_erin")
    a = _make_calendar(client, token, "A")
    _make_calendar(client, token, "B")

    r = client.patch(
        "/calendar/reorder",
        json={"calendar_ids": [a["id"]]},
        headers=auth_headers(token),
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["error_code"] == "INVALID_CALENDAR_ORDER"


def test_reorder_rejects_a_calendar_the_caller_does_not_own(client):
    """A stale client-side list must not be able to re-add a calendar the
    caller left or never belonged to, nor reorder someone else's."""
    alice = register_and_login(client, "cal_order_frank")
    bob = register_and_login(client, "cal_order_grace")

    alice_cal = _make_calendar(client, alice, "Alice's")
    bob_cal = _make_calendar(client, bob, "Bob's")

    r = client.patch(
        "/calendar/reorder",
        json={"calendar_ids": [alice_cal["id"], bob_cal["id"]]},
        headers=auth_headers(alice),
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["error_code"] == "INVALID_CALENDAR_ORDER"


def test_reorder_rejects_duplicate_ids(client):
    """Same length as the caller's real list, but naming one calendar twice
    and omitting another — must not be treated as a valid full ordering."""
    token = register_and_login(client, "cal_order_heidi")
    a = _make_calendar(client, token, "A")
    _make_calendar(client, token, "B")

    r = client.patch(
        "/calendar/reorder",
        json={"calendar_ids": [a["id"], a["id"]]},
        headers=auth_headers(token),
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["error_code"] == "INVALID_CALENDAR_ORDER"


def test_reorder_requires_authentication(client):
    r = client.patch("/calendar/reorder", json={"calendar_ids": []})
    assert r.status_code == 401
