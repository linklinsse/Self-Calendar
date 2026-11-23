"""
Category icons are stored server-side.

They used to live only in each client's localStorage, so any browser or
device that had not picked the icon itself showed every category with the
same default icon. These pin the round-trip through the API.
"""

from tests.conftest import auth_headers, register_and_login


def _make_calendar(client, token):
    r = client.post(
        "/calendar/",
        json={"title": "Cal", "color": "#ffffff"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _make_category(client, token, calendar_id, **extra):
    return client.post(
        "/category/",
        json={"calendar_id": calendar_id, "title": "Work", "color": "#000000", **extra},
        headers=auth_headers(token),
    )


def test_icon_round_trips_through_create_get_and_list(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)

    r = _make_category(client, token, calendar_id, icon="💼")
    assert r.status_code == 201, r.text
    category = r.json()
    assert category["icon"] == "💼"

    r = client.get(f"/category/{category['id']}", headers=auth_headers(token))
    assert r.json()["icon"] == "💼"

    r = client.get(f"/category/calendar/{calendar_id}", headers=auth_headers(token))
    assert [c["icon"] for c in r.json()] == ["💼"]


def test_icon_defaults_to_null_when_omitted(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)

    r = _make_category(client, token, calendar_id)
    assert r.status_code == 201, r.text
    assert r.json()["icon"] is None


def test_patch_icon_only_leaves_other_fields_alone(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    category = _make_category(client, token, calendar_id, icon="💼").json()

    r = client.patch(
        f"/category/{category['id']}",
        json={"icon": "🎨"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["icon"] == "🎨"
    assert r.json()["title"] == "Work"
    assert r.json()["color"] == "#000000"


def test_patch_without_icon_keeps_it(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)
    category = _make_category(client, token, calendar_id, icon="💼").json()

    r = client.patch(
        f"/category/{category['id']}",
        json={"title": "Office"},
        headers=auth_headers(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["icon"] == "💼"


def test_multi_code_point_emoji_is_accepted(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)

    # Woman technologist, medium skin tone: 4 code points (ZWJ sequence).
    r = _make_category(client, token, calendar_id, icon="👩🏽‍💻")
    assert r.status_code == 201, r.text
    assert r.json()["icon"] == "👩🏽‍💻"


def test_oversized_icon_is_rejected(client):
    token = register_and_login(client, "alice")
    calendar_id = _make_calendar(client, token)

    r = _make_category(client, token, calendar_id, icon="x" * 17)
    assert r.status_code == 422, r.text
