"""
End-to-end HTTP smoke test over the real routes: register, login, create a
calendar, create a category, create a recurring event, exclude one
occurrence, edit the event, delete the calendar.

This is the formalized version of the manual TestClient flow described in
review.md §4 — the one that caught every category endpoint being 100%
broken when static analysis (ruff, svelte-check, read-through) had missed
it. Run this after any API change, not just static analysis.
"""

import time

from tests.conftest import auth_headers, register_and_login


def test_full_flow(client):
    token = register_and_login(client, "smoke_user")
    h = auth_headers(token)

    me = client.get("/auth/me", headers=h)
    assert me.status_code == 200
    assert me.json()["username"] == "smoke_user"

    # Calendar
    r = client.post(
        "/calendar/",
        json={"title": "Smoke Calendar", "description": "d", "color": "#ffffff"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    calendar = r.json()
    assert calendar["user_right"] == "O"
    cal_id = calendar["id"]

    # Category
    r = client.post(
        "/category/",
        json={"calendar_id": cal_id, "title": "Work", "color": "#123456"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    cat_id = r.json()["id"]

    # Recurring event
    now = int(time.time())
    r = client.post(
        "/event/",
        json={
            "calendar_id": cal_id,
            "title": "Weekly sync",
            "date_start": now,
            "date_end": now + 3600,
            "category_id": cat_id,
            "obj_recurence": {"type": "W", "interval": 1, "endType": "N"},
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    event = r.json()
    event_id = event["id"]
    assert event["obj_recurence"]["type"] == "W"

    # Exclude one occurrence
    r = client.delete(f"/event/{event_id}/{now}", headers=h)
    assert r.status_code == 200, r.text

    # Edit an unrelated field — recurrence must survive (see review.md §4)
    r = client.patch(f"/event/{event_id}", json={"title": "Weekly sync (renamed)"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["obj_recurence"] is not None
    assert r.json()["title"] == "Weekly sync (renamed)"

    # ...and so must its exceptions. The web client always resends the full
    # recurrence on a PATCH, so replay that exact shape: an unchanged rule
    # must not be treated as a replacement.
    r = client.patch(
        f"/event/{event_id}",
        json={
            "title": "Weekly sync (renamed twice)",
            "obj_recurence": {"type": "W", "interval": 1, "endType": "N"},
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["obj_recurence"]["obj_exceptions"]) == 1, (
        "editing a recurring event must not drop its excluded occurrences"
    )

    # A genuine rule change replaces the row but carries the exclusions over.
    r = client.patch(
        f"/event/{event_id}",
        json={"obj_recurence": {"type": "D", "interval": 2, "endType": "N"}},
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["obj_recurence"]["type"] == "D"
    assert len(r.json()["obj_recurence"]["obj_exceptions"]) == 1

    # Range query picks it up
    r = client.get(f"/event/range?calendar_ids={cal_id}", headers=h)
    assert r.status_code == 200
    assert any(e["id"] == event_id for e in r.json())

    # Delete the calendar — cascades events/recurrences/exceptions/categories/memberships
    r = client.delete(f"/calendar/{cal_id}", headers=h)
    assert r.status_code == 200, r.text

    r = client.get(f"/event/{event_id}", headers=h)
    assert r.status_code == 404
