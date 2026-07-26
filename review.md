# Project review notes

Living notes from a full read-through of the codebase (api + app). Purpose: orient quickly on a new session, know where features actually live, and know the current state of known issues so I don't repeat wrong assumptions.

Last full review: **2026-07-26**, against commit `0946dad` ("todo updated") plus this session's fixes (see §4). Re-validate if a lot of code has changed since.

---

## 1. Where things live (quick index)

### API (`api/app/`)
| Concern | File(s) |
|---|---|
| App wiring / lifespan / router registration | `app.py` |
| Settings (.env) | `common/config.py`, real values in `conf/.env` |
| Auth (JWT, password hashing) | `common/security.py`, `services/auth_service.py`, `routing/auth_routing.py` |
| Request-scoped current user | `common/contexts/logged_user_context.py` + `common/dependencies/verify_logged_user_dependency.py` |
| Permission check helper | `common/utils/verify_user_right_calendar.py` |
| Centralized error catalogue | `common/errors.py` — every HTTP error should go through `raise_app_error(AppErrorCode.X)`. |
| Rate limiting (login/register brute force) | `common/middleware/rate_limit_middleware.py` — in-memory, per-IP, resets on restart, not shared across workers. |
| Calendars (incl. `user_right` on responses) | `models/obj_calendar_model.py`, `services/obj_calendar_service.py` (`_to_schema`/`_resolve_user_right`), `routing/calendar_routing.py` |
| Membership / sharing | `models/lnk_user_calendar_model.py`, `services/lnk_user_calendar_service.py`, `routing/user_calendar_routing.py` |
| Events (CRUD + range query) | `models/obj_event_model.py`, `services/obj_event_service.py`, `routing/event_routing.py` |
| **Recurring events** (working — see §4) | `models/obj_event_recurence_model.py`, `models/obj_event_recurence_exception_model.py`, `schemas/obj_event_recurence_schema.py`, `schemas/obj_event_recurence_exception_schema.py`, `services/obj_event_recurente_service.py` (uses `python-dateutil`) |
| Categories | `models/obj_category_model.py`, `services/obj_category_service.py`, `routing/category_routing.py` |

### App (`app/src/`)
| Concern | File(s) |
|---|---|
| Root shell / session restore | `routes/+page.svelte` |
| Layout (SPA mode: `ssr=false`, `prerender=true`) | `routes/+layout.ts`, `routes/+layout.svelte` |
| App chrome | `components/AppShell.svelte`, `Sidebar.svelte`, `Topbar.svelte`, `BottomNav.svelte` |
| Calendar views | `components/calendar/{MonthView,WeekView,DayView,CalendarBody}.svelte` |
| Event create/edit/detail | `components/event/{EventPanel,EventModal}.svelte` |
| Sidebar filters | `components/sidebar/{CalendarList,CategoryList}.svelte` |
| Settings modal | `components/settings/{CalendarSettings,CategoryEditor,ThemePicker}.svelte` |
| Reactive stores (public API = `lib/stores/index.js`) | `lib/stores/{auth,ui,events,calendars,categories}.js` |
| HTTP layer | `lib/services/{api,auth.service,calendar.service,category.service,event.service}.js` |
| Date/time/recurrence math (pure functions) | `lib/utils.js` — `getOccurrencesInRange`, `expandEventsForRange`, `_nextOccurrence`, `describeRecurrence`, `computeColumns` (side-by-side overlap layout), etc. |
| Themes (5: blushNoir, sageDusk, midnightInk, oceanBreeze, electricYellow) | `lib/themes/{index,blushNoir,sageDusk,midnightInk,oceanBreeze,electricYellow,tokens}.js` |
| Android home-screen widget sync | `lib/widgetSync.js` — documented in `app/README.md` |
| Config / env resolution | `lib/config.js` |

`lib/stores.js` (compat shim) and `lib/theme.js` (legacy single-theme file) were confirmed unused and deleted this session — don't recreate them; import from `lib/stores/index.js` and `lib/themes/index.js` directly.

---

## 2. Actual API surface (verified against routing files)

- `POST /auth/login`, `POST /auth/register` (gated by `USER_CREATION`), `GET /auth/me`
- `PATCH /user/password`
- `POST/GET /calendar/`, `GET/PATCH/DELETE /calendar/{id}` — every response includes `user_right` (the caller's `R`/`W`/`O` on that calendar). `DELETE` cascades: removes the calendar's events (+ recurrences/exceptions), categories, and memberships in the same transaction (see §4).
- `POST /event/`, `GET /event/range` (query params `calendar_ids`/`category_ids`, repeatable; `from_date`/`to_date`), `GET/PATCH/DELETE /event/{id}`
- `DELETE /event/{event_id}/{date}` — adds a **recurrence exception** (removes one occurrence of a recurring series without deleting the series)
- `POST/GET /category/`, `GET /category/calendar/{calendar_id}`, `GET/PATCH/DELETE /category/{id}` — server stores `title`/`color`/`calendar_id`; no `icon` column (client keeps that locally, see app §1)
- `POST/GET /user_calendar/`, etc. — membership management

Event create/edit bodies can carry an embedded `obj_recurence` object. Creating a recurring event and editing an unrelated field (title, color, etc.) on one both now work correctly (see §4 — both were broken before this session). Editing an event WITH a new `obj_recurence` still replaces the recurrence rule wholesale (deletes the old row, creates a new one) rather than patching in place — that's a known efficiency gap, not a bug (see §5).

`api/README.md` and `app/README.md` are up to date as of this review — trust them first; come back here only for things they intentionally don't cover (rationale, history, deferred decisions).

---

## 3. TODO file cross-check

- "On login categories doesn't load" — **fixed this session**: `category.service.js` now syncs `label`/`color`/`calendar_id` from the real `/category` API instead of `localStorage`, and `stores/index.js` loads calendars before categories (categories are fetched per-calendar). Safe to remove from `TODO`.
- "Add Theme Yellow" — done as `electricYellow` (pre-existing, just wasn't documented — now is). Safe to remove from `TODO`.
- "Add Theme unicorn" — no `unicorn` theme file exists; still open.
- Design items (event color not sent, title visibility, color picker hidden by default, category icon selection) — not verified this session; would need to trace `EventPanel.svelte` / `CategoryEditor.svelte` to confirm current state before acting.
- Other `TODO` items (jump-to-month button, default event creation date/hour on click) — not investigated this session.

---

## 4. Fixed this session (2026-07-26)

A full bug/lint/refactor sweep (`ruff check`, `svelte-check`, manual read-through) found and fixed:

**API — bugs:**
- **Creating any recurring event crashed the API.** `obj_event_recurente_service.py::create_event_recurence` passed the `ObjEventRecurenceModel` *class* instead of the built instance into `compute_estimated_end`, so `recurrence.endType == 'N'` evaluated as a SQLAlchemy `BinaryExpression` and `if` on it raised `TypeError`. Fixed by passing the instance. Verified with a smoke test (weekly + monthly recurring events both create successfully now).
- `timedelta` and `relativedelta` were used but never imported in `compute_estimated_end` (would have crashed count-limited monthly/yearly recurrences even after the fix above). Added the imports and `python-dateutil` as a real dependency (`pyproject.toml`).
- `HTTPException`/`status` were used but never imported in `delete_event_recurence`'s 404 branch. Added the imports.
- `edit_event` deleted a recurring event's recurrence on ANY edit (even just the title), because the deletion was unconditional on the event already having one rather than conditional on a replacement being provided. Fixed: the old recurrence is now only deleted when `edited_event.obj_recurence` is actually provided. Verified with a smoke test (title-only edit now preserves the recurrence).
- `ObjCalendarModel.user_right` was a `ClassVar` never populated anywhere. Added a real `user_right` field to `ObjCalendarSchemaComplete`, computed in `obj_calendar_service.py` (`_resolve_user_right`/`_to_schema`) and returned on create/get/get_all/edit.
- The dev `conf/.env` and `conf/.env.template` had `RATE_LIMIT_MAX_FAILURES: int = 5` / `RATE_LIMIT_TIMEOUT_SECONDS: int = 180` (invalid dotenv syntax — Python type-annotation syntax pasted in by mistake). python-dotenv silently skipped both lines; the settings fell back to matching defaults, so this was a latent bug (changing either value in `.env` would have had no effect). Fixed to plain `KEY=value`.
- `ruff check .` is fully clean (was 28 errors): fixed E711 (`!= None`/`== None`), E701 (multi-statement `match/case` lines), E402 (import order in `db_connection.py`), F401 (5 unused imports), and quieted the SQLModel forward-ref F821s with `TYPE_CHECKING` blocks in `obj_calendar_model.py`/`obj_event_recurence_model.py`.
- **Every category API call crashed.** `obj_category_service.py` called `verify_user_right_calendar(user_id=..., calendar_id=..., required_right=...)` on all 5 operations (create/get/list/update/delete) — but the real signature is `(db_user, db_calendar, needed_right)`, positional, where the second arg must be an `ObjCalendarModel` *instance*, not a string id. `TypeError: unexpected keyword argument 'user_id'` on every call. **This was missed by the original static review** (ruff/svelte-check/read-through) and only surfaced when an HTTP-level smoke test (`TestClient` hitting real routes end-to-end) was run to double-check the earlier fixes — worth doing that kind of test after any API change, not just static analysis. Fixed by fetching the calendar first and calling with the correct positional args.
- **`DELETE /calendar/{id}` crashed for any calendar with members or events** (i.e. always, since every calendar has at least the creator's Owner membership row). SQLAlchemy's default relationship behavior tries to `NULL` out child foreign keys (`lnk_user_calendar.calendar_id`, `obj_event.calendar_id`) before deleting the parent; both are `NOT NULL` columns, so the delete raised `IntegrityError`. This is a stronger finding than the previously-documented "no cascade deletes" limitation, which described silent orphaning — it actually always 500s. Fixed: `delete_calendar` now explicitly deletes the calendar's events (+ their recurrences/exceptions), categories, and memberships before deleting the calendar itself. Same underlying pattern also broke `delete_event_recurence` when the recurrence had exceptions attached (`obj_event_recurence_exception.recurrence_id` is also `NOT NULL`) — fixed the same way.
- **Replacing a recurring event's rule via a true partial PATCH crashed** if the request didn't also resend `date_start` (`edit_event` passed `edited_event.date_start`, which is `None` when omitted, straight into `compute_estimated_end` → `datetime.fromtimestamp(None)` → `TypeError`). Not reachable via the app today (it always resends the full event on save — see §2), but a real bug for any other API client doing a genuine partial update. Fixed: falls back to `db_event.date_start` when the payload doesn't include one.
- All of the above verified via `TestClient`-based HTTP smoke tests exercising the real routes (register → login → create calendar → create category → create recurring event → exclude an occurrence → edit the recurrence without `date_start` → delete the calendar), not just direct service-function calls.

**App — bugs:**
- Calendar-permission gating was dead code: `Calendar` objects never carried a `right` field, so `CalendarList.svelte`'s gear icon and `EventModal.svelte`'s edit/delete/read-only badge were shown to every user regardless of actual permission. Fixed end-to-end: API now returns `user_right`, `calendar.service.js` maps it to `right` (`'R'|'W'|'O'`, matching the API's `CalendarRight` codes — the old `'read'|'write'|'admin'` word-form checks never matched anything), and the three call sites (`CalendarList.svelte:89`, `EventModal.svelte:52,133`) now check the real value.
- `stores/events.js::saveEvent` called an undefined `nextId()` in a dead fallback path (`ReferenceError` if `createEvent()` ever resolved falsy). Removed the dead fallback.
- `event.service.js::fetchEvents` sent a `category_id` (singular) query param the API never reads (`category_ids`, plural, is the real one). Fixed the param name and made it accept `categoryIds: string[]`, consistent with `calendarIds`.
- `EventModal.svelte::onDelete` checked `ev.recurrence_id || ev.recurrence`; `recurrence_id` is never set anywhere on the client `CalEvent` shape (dead condition). Simplified to just `ev.recurrence`.
- Confirmed `lib/theme.js` and `lib/stores.js` were dead/near-dead code: `theme.js` had zero importers (deleted); `stores.js` had exactly one remaining importer (`MiniCalendar.svelte`), repointed to `stores/index.js`, then deleted.

**Docs:** `api/README.md`, `app/README.md`, and root `README.md` updated to match all of the above — recurrence/category/permission claims, event route shape, theme list, project structure trees. See those files directly rather than duplicating their content here.

---

## 5. Still open / deferred (not fixed this session — deliberate scope cuts)

- **No FK constraint from `ObjEventModel.category_id` to `obj_category`.** Deleting a calendar now cascades correctly (see §4), but deleting a single category directly (`DELETE /category/{id}`) still leaves any events that reference it with a dangling `category_id` — no crash, just a silent orphan. Deferred because fixing it needs a product decision (block deletion if events reference the category? null out `category_id` on delete?), not just a schema tweak.
- **Recurrence edits always replace the rule wholesale** (delete old `ObjEventRecurenceModel` row, insert a new one) rather than patching in place — functionally correct now (see §4) but churns rows on every save of a recurring event. `obj_event_recurente_service.py` has a commented-out `update_event_recurence` as a starting point. Matches the "opti recurence" TODO/commit — a known, accepted efficiency gap, not a bug.
- **Categories: icon is still client-only.** `category.service.js` now syncs label/color/calendar_id through the real API (see §4), but `icon` has no server column, so it's kept in a `localStorage` overlay keyed by category id. A category created on one device shows up elsewhere with the right label/color but a default icon until re-picked. Documented in `app/README.md`. Would need a schema migration (`obj_category` has no migration tooling — tables are created via `SQLModel.metadata.create_all`, which won't add columns to the existing `dev.db`) to fully fix — deliberately deferred.
- **No test suite** anywhere in the repo despite `make test`/pytest and `svelte-check` being wired up. Not addressed this session (writing a test suite is a much larger, separate task).
- **`svelte-check` still reports ~427 pre-existing errors** across the app (implicit-`any` params, unguarded possibly-null values, `catch (e)` typed `unknown` used as `.message`, a couple of a11y label warnings). Not chased down wholesale — the codebase has never run type-clean and most of these are cosmetic. Fix opportunistically when touching a file that has them, not as a dedicated pass, unless asked.
- Design/TODO items not verified this session (event color not sent, title visibility/contrast, color picker hidden by default, category icon selection UX, jump-to-month button, default date/hour on event creation) — see §3.

---

## 6. How to use this file going forward

- Treat this as a working index, not a changelog — update sections in place rather than appending dated entries, except for the "Last full review" line at the top and the "Fixed this session" §4 (replace its contents wholesale on the next big fix pass rather than appending a second dated block under it).
- `api/README.md` / `app/README.md` are accurate as of this review — if a claim here (§1/§2) ever contradicts them, re-verify against source before trusting either.
- If a future session picks up one of the §5 deferred items, move it out of §5 and into a new §4-equivalent "fixed" note once done, the same way this session's fixes were recorded.
