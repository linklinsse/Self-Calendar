"""
test_permission_matrix.py
-------------------------
Every calendar-scoped endpoint × every permission level, asserted
systematically.

This is different in kind from test_permissions.py, which pins specific bugs
that were found. Those tests can only ever catch what somebody already
thought to look for — the `recurence_id` privilege escalation existed
because one field on one schema was writable, and it was found by reading
that file on the right day. Nothing failed until a test was written for it
specifically.

This file inverts that. It states the rule once, as a table, and checks the
whole surface against it. A new endpoint that forgets its permission check
fails here without anyone needing to suspect it.

THE MODEL
---------
Rights are ordered R < W < O. A check for "R" passes for R, W and O; a check
for "W" passes for W and O; "O" passes only for O.

A caller with no membership at all gets 404, not 403 — deliberately, so the
API does not confirm that a calendar or event exists to someone with no
business knowing. That anti-enumeration choice is asserted here rather than
assumed, because it looks like a bug to anyone reading the route in
isolation, and "fixing" it to 403 would leak existence.

WHAT THIS DOES NOT COVER
------------------------
Field-level authority. This matrix answers "which calendar may I touch",
which is what verify_user_right_calendar decides. It does not answer "which
fields may I set", and the `recurence_id` bug was the second question, not
the first. test_server_owned_fields_are_not_client_settable below covers
that separately — the two questions are independent and both need asserting.
"""

import time

import pytest

from tests.conftest import auth_headers, register_and_login

# Right levels a caller can hold, plus "no membership at all".
ALL_LEVELS = ["O", "W", "R", None]


def _make_calendar(client, token, title="Matrix calendar"):
    r = client.post(
        "/calendar/",
        json={"title": title, "description": "d", "color": "#ffffff"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    return r.json()


def _user_id(client, token):
    return client.get("/auth/me", headers=auth_headers(token)).json()["id"]


@pytest.fixture
def world(client):
    """An owner's calendar with one event, one category, and a second user
    whose membership level the tests vary.

    Built once per test rather than per level: granting and revoking a
    membership between assertions would let one level's side effects leak
    into the next.
    """
    owner_token = register_and_login(client, "matrix_owner")
    other_token = register_and_login(client, "matrix_other")
    # A third account that starts with no membership, so the "grant access"
    # endpoint has someone to grant it to.
    register_and_login(client, "matrix_third")
    owner_h = auth_headers(owner_token)

    calendar = _make_calendar(client, owner_token)
    now = int(time.time())

    r = client.post(
        "/category/",
        json={"calendar_id": calendar["id"], "title": "Work", "color": "#123456"},
        headers=owner_h,
    )
    category = r.json()

    r = client.post(
        "/event/",
        json={
            "calendar_id": calendar["id"],
            "title": "Recurring",
            "date_start": now,
            "date_end": now + 3600,
            "obj_recurence": {"type": "D", "interval": 1, "endType": "N"},
        },
        headers=owner_h,
    )
    assert r.status_code == 200, r.text
    event = r.json()

    # The owner's own membership, used as the target of membership routes.
    r = client.get(f"/user_calendar/all/{calendar['id']}", headers=owner_h)
    owner_membership = r.json()[0]

    return {
        "owner_token": owner_token,
        "other_token": other_token,
        "other_id": _user_id(client, other_token),
        "calendar": calendar,
        "category": category,
        "event": event,
        "owner_membership": owner_membership,
        "now": now,
    }


def _grant(client, world, level):
    """Give the second user `level` on the calendar, or nothing if None.

    Returns the membership id, so tests can target it.
    """
    if level is None:
        return None
    r = client.post(
        "/user_calendar/",
        json={
            "calendar_id": world["calendar"]["id"],
            "username": "matrix_other",
            "right": level,
        },
        headers=auth_headers(world["owner_token"]),
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _assert_allowed(response, label, level):
    assert response.status_code < 400, (
        f"{label}: a caller with right={level} should be allowed, "
        f"got {response.status_code} {response.text[:200]}"
    )


def _assert_denied(response, label, level):
    """Denied — and, for a non-member, denied *without confirming existence*.

    Two different requirements, only one of which is security-critical:

    * A caller with **no membership** must get 404. A 403 would confirm the
      calendar or event exists, which is exactly what the 404-not-403 choice
      elsewhere exists to prevent — and it is comparable, since GET on the
      same id answers 404. This is asserted strictly.

    * A caller who **is a member but outranked** may get either 403 or 404.
      They already know the resource exists, so neither leaks anything. The
      codebase is genuinely split here — resource routes answer 404 via
      EVENT_NOT_FOUND / CALENDAR_NOT_FOUND, membership and owner routes
      answer 403 INSUFFICIENT_RIGHTS — and both are defensible. Pinning one
      would be asserting a preference, not a rule, so this accepts both.
      Worth unifying one day for API consistency; not a security matter.
    """
    if level is None:
        assert response.status_code == 404, (
            f"{label}: a caller with NO membership must get 404, not "
            f"{response.status_code}. Anything else confirms the resource "
            f"exists to someone who should not be able to tell. "
            f"Body: {response.text[:200]}"
        )
        return

    assert response.status_code in (403, 404), (
        f"{label}: a caller with right={level} should be denied, "
        f"got {response.status_code} {response.text[:200]}"
    )


# ── The table ────────────────────────────────────────────────────────────
#
# (label, minimum right required, request builder)
#
# Each builder takes (client, world, membership_id) and performs the call.
# Read operations come first, then writes, then owner-only operations.

def _requests():
    return [
        # ── Read ("R") ──────────────────────────────────────────────
        ("GET /calendar/{id}", "R",
         lambda c, w, m, h: c.get(f"/calendar/{w['calendar']['id']}", headers=h)),

        ("GET /event/{id}", "R",
         lambda c, w, m, h: c.get(f"/event/{w['event']['id']}", headers=h)),

        ("GET /event/range", "R",
         lambda c, w, m, h: c.get(
             f"/event/range?calendar_ids={w['calendar']['id']}", headers=h)),

        ("GET /category/{id}", "R",
         lambda c, w, m, h: c.get(f"/category/{w['category']['id']}", headers=h)),

        ("GET /category/calendar/{id}", "R",
         lambda c, w, m, h: c.get(
             f"/category/calendar/{w['calendar']['id']}", headers=h)),

        ("GET /user_calendar/all/{calendar_id}", "R",
         lambda c, w, m, h: c.get(
             f"/user_calendar/all/{w['calendar']['id']}", headers=h)),

        # ── Write ("W") ─────────────────────────────────────────────
        ("POST /event/", "W",
         lambda c, w, m, h: c.post("/event/", json={
             "calendar_id": w["calendar"]["id"], "title": "New",
             "date_start": w["now"], "date_end": w["now"] + 60,
         }, headers=h)),

        ("PATCH /event/{id}", "W",
         lambda c, w, m, h: c.patch(
             f"/event/{w['event']['id']}", json={"title": "Edited"}, headers=h)),

        ("DELETE /event/{id}/{date}", "W",
         lambda c, w, m, h: c.delete(
             f"/event/{w['event']['id']}/{w['now']}", headers=h)),

        ("POST /category/", "W",
         lambda c, w, m, h: c.post("/category/", json={
             "calendar_id": w["calendar"]["id"], "title": "New cat",
             "color": "#abcdef",
         }, headers=h)),

        ("PATCH /category/{id}", "W",
         lambda c, w, m, h: c.patch(
             f"/category/{w['category']['id']}",
             json={"title": "Renamed"}, headers=h)),

        # ── Owner ("O") ─────────────────────────────────────────────
        ("PATCH /calendar/{id}", "O",
         lambda c, w, m, h: c.patch(
             f"/calendar/{w['calendar']['id']}",
             json={"title": "Renamed"}, headers=h)),

        # Adds a *third* user, not one who already has a membership — the
        # unique constraint would otherwise make the owner case fail with 409
        # for reasons that have nothing to do with permissions.
        ("POST /user_calendar/", "O",
         lambda c, w, m, h: c.post("/user_calendar/", json={
             "calendar_id": w["calendar"]["id"],
             "username": "matrix_third",
             "right": "R",
         }, headers=h)),
    ]


RIGHT_ORDER = {"R": 0, "W": 1, "O": 2}


def _satisfies(held, required):
    """True when `held` meets or exceeds `required`. Mirrors _RIGHT_ORDER in
    app/common/utils/verify_user_right_calendar.py — stated independently
    here on purpose, so a change to that ordering has to be made twice and
    thought about once."""
    if held is None:
        return False
    return RIGHT_ORDER[held] >= RIGHT_ORDER[required]


@pytest.mark.parametrize("level", ALL_LEVELS)
@pytest.mark.parametrize(
    "label,required,call",
    _requests(),
    ids=[r[0] for r in _requests()],
)
def test_permission_matrix(client, world, label, required, call, level):
    """Every endpoint, at every right level, against the stated rule."""
    membership_id = _grant(client, world, level)
    headers = auth_headers(world["other_token"])

    response = call(client, world, membership_id, headers)

    if _satisfies(level, required):
        _assert_allowed(response, label, level)
    else:
        _assert_denied(response, label, level)


# ── Destructive operations, tested separately ────────────────────────────
#
# Kept out of the table above because each destroys the fixture it acts on,
# so they cannot share a parametrised world with the read/write cases
# without ordering effects.

@pytest.mark.parametrize("level", ALL_LEVELS)
def test_delete_event_requires_write(client, world, level):
    _grant(client, world, level)
    r = client.delete(
        f"/event/{world['event']['id']}",
        headers=auth_headers(world["other_token"]),
    )
    if _satisfies(level, "W"):
        _assert_allowed(r, "DELETE /event/{id}", level)
    else:
        _assert_denied(r, "DELETE /event/{id}", level)


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_delete_category_requires_write(client, world, level):
    _grant(client, world, level)
    r = client.delete(
        f"/category/{world['category']['id']}",
        headers=auth_headers(world["other_token"]),
    )
    if _satisfies(level, "W"):
        _assert_allowed(r, "DELETE /category/{id}", level)
    else:
        _assert_denied(r, "DELETE /category/{id}", level)


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_delete_calendar_requires_owner(client, world, level):
    _grant(client, world, level)
    r = client.delete(
        f"/calendar/{world['calendar']['id']}",
        headers=auth_headers(world["other_token"]),
    )
    if _satisfies(level, "O"):
        _assert_allowed(r, "DELETE /calendar/{id}", level)
    else:
        _assert_denied(r, "DELETE /calendar/{id}", level)


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_membership_read_requires_read(client, world, level):
    """GET /user_calendar/{id} — the endpoint whose missing authorization was
    a finding in the 2026-07-28 review. Covered by the matrix now rather than
    by a single regression test."""
    _grant(client, world, level)
    r = client.get(
        f"/user_calendar/{world['owner_membership']['id']}",
        headers=auth_headers(world["other_token"]),
    )
    if _satisfies(level, "R"):
        _assert_allowed(r, "GET /user_calendar/{id}", level)
    else:
        # This route returns MEMBERSHIP_NOT_FOUND (404) for an outranked
        # member too, not 403 — memberships reveal who else has access, so
        # existence is itself the sensitive part.
        assert r.status_code == 404, r.text


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_membership_edit_requires_owner(client, world, level):
    membership_id = _grant(client, world, level)
    # Target the *other* user's own membership where one exists, so the
    # last-owner guard is not what produces the failure.
    target = membership_id or world["owner_membership"]["id"]
    r = client.patch(
        f"/user_calendar/{target}",
        json={"right": "R"},
        headers=auth_headers(world["other_token"]),
    )
    if _satisfies(level, "O"):
        _assert_allowed(r, "PATCH /user_calendar/{id}", level)
    else:
        _assert_denied(r, "PATCH /user_calendar/{id}", level)


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_membership_delete_requires_owner(client, world, level):
    membership_id = _grant(client, world, level)
    target = membership_id or world["owner_membership"]["id"]
    r = client.delete(
        f"/user_calendar/{target}",
        headers=auth_headers(world["other_token"]),
    )
    if _satisfies(level, "O"):
        _assert_allowed(r, "DELETE /user_calendar/{id}", level)
    else:
        _assert_denied(r, "DELETE /user_calendar/{id}", level)


# ── Field-level authority ────────────────────────────────────────────────

def test_server_owned_fields_are_not_client_settable(client, world):
    """The question the matrix above does not ask.

    verify_user_right_calendar decides *which calendar* a caller may touch.
    It says nothing about *which fields* they may set, and the recurence_id
    escalation lived entirely in that gap: the permission check passed
    correctly, and the request then set a field it had no business setting.

    Asserting the schemas directly rather than the HTTP behaviour, because
    the point is that these fields are not part of the contract at all — a
    field that is silently ignored today becomes a bug the moment someone
    "helpfully" wires it up.
    """
    from app.schemas.obj_event_schema import (
        ObjEventSchemaCreate,
        ObjEventSchemaEdit,
    )

    server_owned = {"recurence_id", "id", "obj_calendar", "obj_recurence_id"}

    for schema in (ObjEventSchemaCreate, ObjEventSchemaEdit):
        leaked = server_owned & set(schema.model_fields)
        assert not leaked, (
            f"{schema.__name__} exposes server-owned field(s) {leaked} to "
            f"clients. recurence_id in particular let any authenticated user "
            f"bind their event to another calendar's recurrence, read its "
            f"rule, and destroy it by deleting their own event."
        )
