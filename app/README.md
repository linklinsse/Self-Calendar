# Self Calendar

A polished, themeable personal calendar app built with **Svelte 5 + SvelteKit**. Runs entirely on sample data out of the box — no backend required.

---

## Quick start

```bash
cd self-calendar
npm install        # requires Node ≥ 20
npm run dev        # → http://localhost:5173
```

Build for production:

```bash
npm run build
npm run preview
```

Checks:

```bash
npm test           # vitest — recurrence expansion (src/lib/*.test.js)
npm run test:watch
npm run check      # svelte-check (has a large pre-existing error baseline)
```

`npm test` is the one to run after touching `src/lib/utils.js`. Its recurrence
suite is a differential test: 2,700 generated cases comparing the optimised
expansion against a deliberately naive reference implementation, across every
combination of rule type, interval, selected weekdays, end condition, event age
and requested range. It exists because that code silently stopped rendering
daily events older than ~4.1 years, and it caught a wrong fix for that bug
before it shipped.

Note that recurrence expansion also has a hand-maintained Kotlin port in
`android/app/src/main/java/app/selfcalendar/app/widget/WidgetDataFetcher.kt`,
which these tests do **not** cover. Change both together — it has drifted twice.

CI runs all of the above on every push — see
[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml).

---

## Changing the backend address

The API address is editable from the **login screen** — expand "Server",
enter an address, Test, then Save. It is stored in this browser's
localStorage under `sc_api_base_url` and overrides both `VITE_API_BASE_URL`
and the `API_BASE_URL` injected by `docker-entrypoint.sh`.

This exists so a fork or a self-hoster does not have to rebuild the bundle
(or the Android app) to point it somewhere else. Resolution order:

1. `localStorage.sc_api_base_url` — set from the login screen
2. `window.__ENV__.API_BASE_URL` — injected at container start
3. `VITE_API_BASE_URL` — build time, `.env.local`
4. `window.location.origin` — same-origin fallback

Two behaviours worth knowing before changing this code:

- **`API_BASE_URL` is resolved once at module load, not per request.**
  Switching backends invalidates the session token, every loaded store and
  the widget's cache, so `setApiBaseUrl()` reloads the page. Making it a live
  lookup would permit a half-switched state with some requests going to each
  server.
- **The stored token is cleared on switch**, because the old server's JWT is
  meaningless to the new one and produces a 401 instead of a login screen.

Remember the API address is often *not* the address of this page — in the
default `docker-compose` setup the web app is on `:8686` and the API on
`:8787`. Whatever origin the web app is served from must also appear in the
API's `CORS_ORIGINS`, or the browser blocks the request and `fetch()` reports
it identically to the server being down. The Test button exists to surface
exactly this.

---

## Device calendar export (Android)

The event modal has an action that copies an event into the device's own
calendar. It opens the system calendar's new-event editor prefilled — title,
time, location, all-day flag, and a real RFC 5545 `RRULE` for recurring
events — with a `selfcalendar://event?id=…` link in the description so the
copy can bring the user back here.

- `src/lib/rrule.js` — internal recurrence → `RRULE`. The mirror image of
  `analyze_recurrence` in the API's Google importer; keep them in step.
- `src/lib/services/systemCalendar.service.js` — builds the payload.
- `android/.../calendar/CalendarBridgePlugin.kt` — fires the intent.

**It is a one-time copy, not a sync.** Editing the event afterwards on either
side does not update the other. Two-way sync would need a sync adapter, or an
ICS subscription feed served by the API — neither exists.

Two things to know if you touch this:

- It uses `ACTION_INSERT`, **not** a direct write to the calendar provider,
  so it needs no `READ_CALENDAR`/`WRITE_CALENDAR` permission and the user
  picks the target calendar. Don't "simplify" it into a direct write without
  weighing that.
- The system editor returns no callback. The app cannot tell whether the user
  saved, which is why the toast says the calendar app is opening rather than
  claiming the event was added.

The `<queries>` element in `AndroidManifest.xml` is load-bearing: without it
`resolveActivity()` returns null on Android 11+ even with a calendar app
installed, and the feature reports "no calendar app" on every modern device.

Or use the Makefile:

```bash
make init     # install all dependencies
make dev      # start dev server
make build    # production build → dist/
make preview  # preview the production build
```

---

## Project structure

```
src/
├── app.html                    ← SvelteKit HTML shell (required)
├── routes/
│   ├── +layout.ts              ← prerender = true, ssr = false (SPA / Capacitor)
│   └── +page.svelte            ← Root page: session restore → AppShell or LoginScreen
│
├── components/
│   ├── LoginScreen.svelte      ← Sign-in form (no register — API has no endpoint)
│   ├── AppShell.svelte         ← Main layout shell (sidebar + topbar + content)
│   ├── Sidebar.svelte          ← Collapsible left sidebar (desktop + mobile drawer)
│   ├── Topbar.svelte           ← Header bar with navigation + hamburger
│   ├── BottomNav.svelte        ← Mobile-only bottom navigation bar
│   │
│   ├── calendar/
│   │   ├── CalendarBody.svelte ← View dispatcher + reactive event reload on nav
│   │   ├── MonthView.svelte    ← Monthly grid
│   │   ├── WeekView.svelte     ← 7-column time grid with side-by-side overlap
│   │   └── DayView.svelte      ← Single-day time grid with side-by-side overlap
│   │
│   ├── event/
│   │   ├── EventPanel.svelte   ← Add / edit drawer (right on desktop, bottom on mobile)
│   │   └── EventModal.svelte   ← Event detail modal (read-only)
│   │
│   ├── sidebar/
│   │   ├── CalendarList.svelte ← Calendar filter + inline create form
│   │   └── CategoryList.svelte ← Category filter grouped by calendar
│   │
│   ├── settings/
│   │   ├── CalendarSettings.svelte ← 3-tab modal: General | Members | Params
│   │   ├── CategoryEditor.svelte   ← Create / edit a category
│   │   └── ThemePicker.svelte      ← Inline theme grid in the sidebar
│   │
│   └── ui/
│       ├── MiniCalendar.svelte ← Date-picker widget used in EventPanel
│       ├── FilterDrawer.svelte ← Mobile filter overlay
│       ├── ViewSwitcher.svelte ← Month / Week / Day tab strip
│       └── Toast.svelte        ← Snackbar notifications
│
└── lib/
    ├── config.js               ← All env-var configuration (API URL, theme, locale, …)
    ├── utils.js                ← Pure date/time/recurrence helpers (locale-aware)
    │
    ├── stores/                 ← Svelte reactive stores
    │   ├── index.js            ← Public store API — the only import path for components
    │   ├── auth.js             ← currentUser, isLoggedIn, authLoading
    │   ├── ui.js               ← view, cursor, overlay states, toast
    │   ├── events.js           ← events list, visibleEvents (filtered + color-resolved), CRUD
    │   ├── calendars.js        ← calendars list, toggle, CRUD
    │   └── categories.js       ← categories list, toggle, CRUD
    │
    ├── services/               ← HTTP service layer
    │   ├── api.js              ← Base fetch client + JWT bearer token handling
    │   ├── auth.service.js     ← login / logout / getMe
    │   ├── calendar.service.js ← Calendar CRUD + user-calendar membership
    │   ├── category.service.js ← Category CRUD via /category (title/color/calendar_id);
    │   │                          icon is a client-only overlay in localStorage (no server column)
    │   └── event.service.js    ← Event CRUD with unix-timestamp serialisation
    │
    ├── widgetSync.js           ← Pushes theme + auth (not events) to the native Android home-screen widget (Capacitor)
    │
    └── themes/                 ← Theme definitions
        ├── index.js            ← Theme registry + activeThemeId store + applyTheme()
        ├── tokens.js           ← Shared font, size, radius, and colour tokens
        ├── blushNoir.js        ← Default (dark rose)
        ├── sageDusk.js         ← Dark mint / forest
        ├── midnightInk.js      ← Deep indigo / lavender
        ├── oceanBreeze.js      ← Dark teal
        └── electricYellow.js   ← Electric yellow
```

---

## Themes

Themes are pure JS objects that define CSS variable values. The active theme is applied at startup via `applyTheme()`, persisted to `localStorage`, and can be changed at runtime through the ThemePicker in the sidebar.

### Switch the default theme

Set `VITE_THEME` in `.env.local`:

```env
VITE_THEME=sageDusk
```

Available theme keys:

| Key               | Accent      | Style                 |
|-------------------|-------------|-----------------------|
| `blushNoir`       | 🌸 Rose      | Dark luxury (default) |
| `sageDusk`        | 🌿 Mint      | Dark forest           |
| `midnightInk`     | 💜 Lavender  | Deep indigo           |
| `oceanBreeze`     | 🩵 Teal      | Dark ocean            |
| `electricYellow`  | ⚡ Yellow    | Electric              |

### Add a custom theme

1. Copy `src/lib/themes/blushNoir.js` → `src/lib/themes/myTheme.js`
2. Adjust the token values in the exported object
3. Register it in `src/lib/themes/index.js`:
   ```js
   import { myTheme } from './myTheme.js';
   export const THEMES = { ..., myTheme };
   ```
4. Set `VITE_THEME=myTheme` or pick it in the ThemePicker UI

---

## Connecting to a real backend

All data flows through the service layer in `src/lib/services/`.

There is no mock/offline mode — the app needs a reachable API to do anything. To point it at one, create `.env.local`:

```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

### Expected API endpoints

| Service                     | Endpoints                                                                         |
|-----------------------------|-----------------------------------------------------------------------------------|
| `auth.service.js`           | `POST /auth/login` → `{ access_token }` · `POST /auth/register` · `GET /auth/me` |
| `calendar.service.js`       | `GET/POST /calendar/` · `GET/PATCH/DELETE /calendar/{id}`                         |
|                             | `GET/POST /user_calendar/` · `GET/PATCH/DELETE /user_calendar/{id}`               |
| `category.service.js`       | `GET /category/calendar/{calendar_id}` · `POST /category/` · `PATCH/DELETE /category/{id}` |
| `event.service.js`          | `POST /event/` · `GET /event/range?calendar_ids=&category_ids=&from_date=&to_date=` |
|                             | `GET/PATCH/DELETE /event/{id}` · `DELETE /event/{id}/{date}` (exclude one occurrence) |

> **Note:** Registration is gated server-side by the `USER_CREATION` setting — if disabled, `POST /auth/register` returns 401 and accounts must be created directly in the database.

### Authentication

The client uses a JWT bearer token stored in `localStorage` under the key `sc_auth_token`. The token is set via `setToken()` from `api.js` on login and is automatically attached as `Authorization: Bearer <token>` to every request. Calling `restoreSession()` on app mount re-hydrates the store from this token so users stay logged in across page reloads.

### Event field names

All events use the canonical API field names throughout the codebase:

| Field         | Type      | Description                              |
|---------------|-----------|------------------------------------------|
| `calendar_id` | `string`  | ID of the owning calendar                |
| `category_id` | `string?` | ID of the assigned category (optional)   |
| `adresse`     | `string?` | Location / address                       |
| `description` | `string?` | Notes / body text                        |
| `date_start`  | `number`  | Unix timestamp (API wire format)         |
| `date_end`    | `number`  | Unix timestamp (API wire format)         |

Internally, `event.service.js` deserialises unix timestamps into `startDate`/`endDate` `Date` objects and `start`/`end` `"HH:MM"` strings for use by the views.

### Calendar membership (`right` field)

| Value | Permissions                                             |
|-------|-----------------------------------------------------------|
| `R`   | View events only                                        |
| `W`   | View + create / edit / delete events                    |
| `O`   | All of `W` + manage members + edit calendar settings    |

These are the API's `CalendarRight` codes (Read/Write/Owner) — used both on `UserCalendar` objects from `/user_calendar/` and as `right` on `Calendar` objects from `/calendar/` (mapped client-side from the API's `user_right` field), representing the current user's own permission on that calendar. UI that gates owner-only actions (e.g. the calendar-settings gear in `CalendarList.svelte`, edit/delete in `EventModal.svelte`) checks against `'O'`/`'W'` directly.

### Categories: what's synced vs. local-only

`category.service.js` persists `label` (→ API `title`), `color`, and `calendar_id` through `/category/` so categories are consistent across devices/logins, same as calendars. The `icon` field has no server-side column — it's kept in a small `localStorage` overlay (keyed by category id) and merged back in on read. A category created on one device will show up elsewhere with its label/color intact but the default icon until re-picked.

---

## Environment variables

All variables can be set in `.env.local` (gitignored) prefixed with `VITE_` for local dev (e.g. `VITE_API_BASE_URL=http://localhost:8000`), or without prefix in Docker via `window.__ENV__`. The `VITE_` prefix is a Vite requirement and is added automatically by `config.js` when looking up build-time values.

| Variable            | Default                     | Description                                     |
|---------------------|-----------------------------|-------------------------------------------------|
| `API_BASE_URL`      | same origin as the page (`window.location.origin`) | Backend API root (no trailing slash). Falls back to same-origin rather than a hardcoded URL, so a broken runtime-injection setup fails obviously instead of silently talking to someone else's server. |
| `THEME`             | `blushNoir`                 | Default theme key                               |
| `APP_NAME`          | `Self Calendar`             | App name shown in tab title + login screen      |
| `DEFAULT_VIEW`      | `month`                     | Starting calendar view: `month` / `week` / `day`|
| `FIRST_DAY_OF_WEEK` | `1` (Monday)                | `0`=Sunday · `1`=Monday · `6`=Saturday         |
| `LOCALE`            | `fr-FR`                     | BCP 47 locale tag for `Intl` date formatting    |
| `HOUR_FORMAT`       | `24`                        | Time display: `12` for AM/PM · `24` for 24-hour |

---

## Mobile (Capacitor)

This app targets Android and iOS via Capacitor. The build output (`dist/`) is synced to the native project folders.

```bash
make android   # build + sync + open Android Studio
make ios       # build + sync + open Xcode
make sync      # sync latest build to native platforms only
```

Requires Android Studio (Android) and Xcode (iOS/macOS only).

### Android home-screen widget

The month-grid widget (`android/app/src/main/java/app/selfcalendar/app/widget/`) fetches its own events directly from the API — it does not depend on anything in the app's in-memory/view-scoped state. `src/lib/widgetSync.js` only pushes two things to the native `WidgetBridge` Capacitor plugin: the active **theme** (`updateTheme`, whenever the user changes it) and the **JWT + API base URL** (`updateAuth`, whenever login state changes). Both calls are no-ops on web/iOS (`Capacitor.isNativePlatform()` guard) and fail silently if the plugin isn't registered.

Native side (`WidgetDataFetcher.kt`): calls `GET /calendar/`, `GET /category/calendar/{id}` (for event colors), and `GET /event/range` itself using the synced token, then expands recurring events into per-day occurrences with a Kotlin port of `utils.js`'s `getOccurrencesInRange`/`_nextOccurrence`. Triggered on widget placement, the periodic `updatePeriodMillis` refresh (`month_widget_info.xml`), the widget's own prev/next month buttons, and on login/logout — each time for whichever month the widget is currently showing. On any fetch failure (offline, no token yet, expired token) it just keeps showing the last successfully fetched data rather than clearing the widget.

This used to work by mirroring the app's `visibleEvents` store, which broke whenever the app navigated to a narrower view (e.g. Day view would make the widget appear to lose events) — the widget fetching its own data sidesteps that entirely.

The synced JWT is stored in its own `EncryptedSharedPreferences`-backed file (`TokenStore.kt`), separate from the rest of `widget_data` prefs (theme/events/api_base_url, not sensitive) — a plain `SharedPreferences` bearer token would otherwise be extractable via `adb backup`/cloud backup. `android:allowBackup` is `false` for the same reason. `android:usesCleartextTraffic="true"` stays global (not scoped to private IP ranges) — Android's `networkSecurityConfig` can't express CIDR ranges, only exact hostnames/IPs, and this app's real deployment story is an arbitrary self-hosted LAN address chosen at build/config time, so scoping it would need to know that address in advance.

### App icon / favicon

The source design is `selfcalendar_favicon_26_pink.svg` (repo root of `app/`) — a design comp with two size previews of the same icon (dark rounded-square card, pink header with two "binder hole" dots, bold pink "26"). The actual usable master is `src/static/favicon.svg` (just the icon, no captions/duplicate previews), used directly as the web favicon (`app.html`: SVG primary, `favicon.png`/`apple-touch-icon.png` as PNG fallbacks for browsers/platforms that need one).

Android's adaptive icon system needs the design split into two layers, not one flat image:
- **Background** — a plain color (`res/values/ic_launcher_background.xml`, `#141414`, matching the card's own background) rather than a raster image.
- **Foreground** — just the header + dots + "26" (no card background/border), scaled to Android's ~66/108 "safe zone" so it isn't clipped by circular/squircle/rounded-square launcher masks. Regenerated at all 5 mipmap densities (`mipmap-{m,h,xh,xxh,xxx}hdpi/ic_launcher_foreground.png`) plus the legacy pre-adaptive-icon `ic_launcher.png`/`ic_launcher_round.png` (the full flat design, for API < 26).

If the design ever changes, regenerate from `favicon.svg` (full icon) and a foreground-only variant (drop the background rect, scale ~0.55 into a 108×108 canvas, center via `translate(21,27)`) — there's no bundled tool for this in the repo; it was done with a one-off Node + `sharp` script, not committed since it's a one-time asset step, not part of the build.

---

## Docker

A multi-stage Dockerfile is included. It builds the static assets and serves them with nginx. `docker-entrypoint.sh` injects `API_BASE_URL`/`THEME`/`HOUR_FORMAT`/etc. into `env-config.js` at container start (read by `config.js`), so the same image works against any backend without rebuilding — built with `jq -n --arg` rather than raw shell interpolation, so a `"`/newline in an env var like `APP_NAME` can't produce broken or injected JS. `nginx.conf` (copied in at build time) adds baseline security headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) — no CSP, since a meaningfully-scoped `connect-src` needs to know the deployment's API origin, which is only set at container start, not at nginx-config time. A `HEALTHCHECK` is defined so `docker-compose.yml`'s `autoheal` labels (and `api`'s `depends_on: condition: service_healthy`) actually mean something — it hits `http://127.0.0.1/`, not `localhost`, since `localhost` resolves to `::1` first inside the container and nginx only listens on IPv4.

```bash
docker build -t self-calendar .
docker run -p 8080:80 -e API_BASE_URL=http://localhost:8082 -e APP_NAME="Self Calendar" self-calendar
# → http://localhost:8080
```

`API_BASE_URL` falls back to the page's own origin (`window.location.origin`) if not set — not a hardcoded URL — so a broken runtime-injection setup fails obviously (network error) instead of silently talking to the wrong server.

For running the app together with the api, prefer `docker compose up -d --build` from the repo root — see the root [`README.md`](../README.md#quick-start-docker--prod-style).

---
