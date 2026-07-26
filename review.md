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
| Android home-screen widget sync (theme + auth only) | `lib/widgetSync.js` — documented in `app/README.md` |
| Config / env resolution | `lib/config.js` |

`lib/stores.js` (compat shim) and `lib/theme.js` (legacy single-theme file) were confirmed unused and deleted this session — don't recreate them; import from `lib/stores/index.js` and `lib/themes/index.js` directly.

### Native Android widget (`app/android/app/src/main/java/app/selfcalendar/app/widget/`)
| Concern | File(s) |
|---|---|
| Widget rendering (month grid, prev/next nav, theme application) | `MonthWidgetProvider.kt` |
| Own API fetch (calendars, categories, events) + recurrence expansion | `WidgetDataFetcher.kt` — Kotlin port of `utils.js`'s occurrence-expansion algorithm, operates on the API's wire format directly |
| JS↔native bridge (`updateTheme`, `updateAuth`) | `WidgetBridgePlugin.kt` |
| Layouts | `res/layout/month_widget*.xml` |

The widget fetches its own data over HTTP — it does **not** share the app's in-memory `visibleEvents`/event cache. See §4 for why that changed and how it's wired. No emulator is available in this environment; every widget change this session was verified with `./gradlew assembleDebug` (compiles + resources link) but never actually run — the user tests on their own device. Flag this explicitly whenever picking up widget work: static compilation success is not proof of runtime correctness here.

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

**Docker / deployment (`docker-compose up` now actually works):**
- `docker-compose.yml` had no `build:` stanza at all — it only referenced pre-built `selfcalendar-web`/`selfcalendar-api` images, so `docker-compose up` alone never worked from a fresh clone. Added `build: {context, dockerfile}` to both services (images still get tagged `selfcalendar-web:latest`/`selfcalendar-api:latest`, matching what `make docker-build` in each sub-project produces).
- The api's volume mounts didn't match where the container actually looks for things: `./conf:/work/app/conf` and `./db/prod.db:/work/app/prod.db`, but `api/Dockerfile` sets `WORKDIR /work` and `common/config.py`'s `env_file="./conf/.env"` (plus `DB_URL=sqlite:///./...`) resolve relative to that CWD — i.e. `/work/conf/...`, not `/work/app/conf/...`. The mounted file was silently never found, so the container always ran on hardcoded defaults (`SECRET_KEY=change-me`, no CORS, `dev.db` inside the image instead of a persisted volume). Fixed the mount paths to `./conf:/work/conf` and `./db:/work/db` (a directory mount for the whole db/ folder, not a single-file mount — avoids Docker auto-creating a directory where `prod.db` was expected if it didn't already exist on the host).
- Neither `./conf/` nor `./db/` existed at the repo root at all. Created both (with a root `.gitignore` for `/conf/.env` and `/db/*`, matching the existing "never commit `.env`" convention — `db/.gitkeep` keeps the empty dir tracked). `conf/.env` is seeded from `api/conf/.env.template` with a freshly-generated `SECRET_KEY` (`openssl rand -hex 32`), `USER_CREATION=True` (so the first account can be created via the app's own register screen — flip to `False` once done), `DB_URL=sqlite:///./db/prod.db`, and `CORS_ORIGINS=["http://localhost:8686"]`.
- **`API_BASE_URL: 'http://api:8082'` was fundamentally wrong** — it's injected into `window.__ENV__` and read *client-side*, in the browser, not server-side (see `docker-entrypoint.sh` / `app/README.md`'s Docker section). `api` is only resolvable as a hostname *inside* the Docker network — a real browser outside it can never reach `http://api:8082`, so the frontend could never talk to the backend no matter how everything else was configured. Fixed by exposing `api`'s port (`8082:8082`) and pointing `API_BASE_URL` at `http://localhost:8082` instead — matches `CORS_ORIGINS` above.
- Verified for real: `docker compose build` (builds both images from source) → `docker compose up -d` → registered a user, logged in, and confirmed CORS headers (`access-control-allow-origin: http://localhost:8686`) via `curl` against both containers → confirmed `prod.db` persisted correctly to the host at `./db/prod.db`. Test data was removed afterward so the repo's `db/` is empty again for a genuine first run.
- Also fixed two related doc bugs found while verifying this: `api/README.md`'s standalone `docker run` example referenced an image tag (`fastapi-app`) that never matched what `make docker-build` actually produces (`selfcalendar-api`); `app/README.md`'s Docker section didn't mention `API_BASE_URL` needing to be set via `-e` for a standalone `docker run` to be useful.

**Android widget (`app/android/.../widget/`), rebuilt across several iterations in a follow-up session:**
- Original widget just showed a small colored dot per event per day, no month navigation at all. Rebuilt to a real month grid with prev/next buttons (broadcast `PendingIntent`s targeting `MonthWidgetProvider` itself, per-widget-id month offset in `SharedPreferences`) and event titles instead of dots.
- **Event title text collapsed to invisible ("just a small 'I'")** — twice, from two different root causes. First: `layout_weight` on a `TextView` inside a `LinearLayout` added via `RemoteViews#addView()` doesn't reliably distribute width in the widget host. Fixed by switching to a `FrameLayout` (accent bar overlaid, title given `match_parent` + a start margin) — didn't fully fix it. Second, deeper cause: event cards were a **3rd level** of dynamically-composed `RemoteViews` (`month_widget` → `month_widget_row` → `month_widget_cell` → `month_widget_event_card`, each added via `addView()`); width propagation through nested `addView()` composition breaks past ~2 levels regardless of weight vs. `match_parent`. Fixed by flattening: 3 fixed event-row "slots" + one overflow line are now declared statically inside `month_widget_cell.xml` itself and toggled with `setViewVisibility`/`setTextViewText`, not built as separate `addView()`'d objects. **If a future widget change reintroduces a 3rd level of `addView()`-composed views, expect this exact symptom again** — prefer fixed static slots over dynamic per-item composition for anything nested this deep.
- **Colors didn't follow the app's selected theme, and non-today day numbers were unreadable in dark themes.** The widget only had 2 static color sets keyed to system light/dark mode, with zero awareness of the app's 5 custom themes — and separately, `MonthWidgetProvider.kt` hardcoded day-number text to `#1A0812` (near-black) unconditionally, so a dark-themed widget showed near-invisible numbers. Fixed by adding a real theme-sync pipeline: `widgetSync.js` pushes `{bg, text, textMuted, accent}` (from `bgSurface`/`text1`/`text2`/`accent` of whichever theme is active) via a new `WidgetBridge.updateTheme()` call, and `MonthWidgetProvider.kt` renders everything (background, day numbers, today-circle, dow labels, event titles) from that instead of hardcoded/static-resource colors. Since RemoteViews can't recolor an arbitrary-hex shape drawable below API 31, the background and today-circle are now small bitmaps generated at render time (`roundedRectBitmap`/`circleBitmap`) rather than static drawables.
- **Biggest one: the widget lost all events whenever the app navigated to a narrower view (e.g. Day view).** Root cause: the widget mirrored the app's `visibleEvents` store verbatim on every change — that store is scoped to whatever's currently displayed, not a stable dataset, so switching views shrank what got pushed. Fixed by removing event-pushing from `widgetSync.js` entirely and giving the widget **its own API client** (`WidgetDataFetcher.kt`): it calls `GET /calendar/`, `GET /category/calendar/{id}` (for colors), and `GET /event/range` directly, using a JWT + `API_BASE_URL` synced once via a new `WidgetBridge.updateAuth()` call (fired on login/logout, not on every event change). Recurring events are expanded into per-day occurrences with a Kotlin port of `utils.js`'s `getOccurrencesInRange`/`_nextOccurrence`, operating on the API's own wire format (type/interval/days-bitmask/endType/count/until/exceptions) rather than the JS-internal format. Fetches happen on: widget placement, the existing periodic `updatePeriodMillis` refresh, the widget's own prev/next clicks (for the newly-shown month), and login/logout. Uses `AppWidgetProvider#goAsync()` + a background `Thread` for the periodic/nav-triggered fetches (required — `onUpdate`/`onReceive` run on the main thread and network calls can't block them); Capacitor already dispatches `@PluginMethod` calls off the main thread, so `updateAuth`'s fetch runs inline. Any fetch failure (offline, no token yet, expired token) just keeps the last successfully-cached render rather than clearing the widget. Added `android:usesCleartextTraffic="true"` to the manifest since this native `HttpURLConnection` code (unlike the WebView) is subject to the app's network security config, and this is an explicitly self-hostable app that may point at a plain-HTTP local `API_BASE_URL` (e.g. the `docker-compose` setup from earlier this session).
- **Not verified on-device** — no emulator available in this environment and the user asked not to try to run one. Every change was checked with `./gradlew assembleDebug` only (compiles, resources link, no more than that). The auth/token-sync path, the `goAsync()` background-fetch timing, and the recurrence-expansion port are the highest-risk untested pieces — check those first if something looks wrong after installing.

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
