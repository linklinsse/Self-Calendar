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

To connect a real API, create `.env.local`:

```env
VITE_MOCK_MODE=false
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

All variables can be set in `.env.local` (gitignored) prefixed with `VITE_` for local dev (e.g. `VITE_MOCK_MODE=false`), or without prefix in Docker via `window.__ENV__`. The `VITE_` prefix is a Vite requirement and is added automatically by `config.js` when looking up build-time values. The defaults work for local development without any backend.

| Variable            | Default                     | Description                                     |
|---------------------|-----------------------------|-------------------------------------------------|
| `API_BASE_URL`      | `http://localhost:3000/api` | Backend API root (no trailing slash)            |
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

### App icon / favicon

The source design is `selfcalendar_favicon_26_pink.svg` (repo root of `app/`) — a design comp with two size previews of the same icon (dark rounded-square card, pink header with two "binder hole" dots, bold pink "26"). The actual usable master is `src/static/favicon.svg` (just the icon, no captions/duplicate previews), used directly as the web favicon (`app.html`: SVG primary, `favicon.png`/`apple-touch-icon.png` as PNG fallbacks for browsers/platforms that need one).

Android's adaptive icon system needs the design split into two layers, not one flat image:
- **Background** — a plain color (`res/values/ic_launcher_background.xml`, `#141414`, matching the card's own background) rather than a raster image.
- **Foreground** — just the header + dots + "26" (no card background/border), scaled to Android's ~66/108 "safe zone" so it isn't clipped by circular/squircle/rounded-square launcher masks. Regenerated at all 5 mipmap densities (`mipmap-{m,h,xh,xxh,xxx}hdpi/ic_launcher_foreground.png`) plus the legacy pre-adaptive-icon `ic_launcher.png`/`ic_launcher_round.png` (the full flat design, for API < 26).

If the design ever changes, regenerate from `favicon.svg` (full icon) and a foreground-only variant (drop the background rect, scale ~0.55 into a 108×108 canvas, center via `translate(21,27)`) — there's no bundled tool for this in the repo; it was done with a one-off Node + `sharp` script, not committed since it's a one-time asset step, not part of the build.

---

## Docker

A multi-stage Dockerfile is included. It builds the static assets and serves them with nginx. `docker-entrypoint.sh` injects `API_BASE_URL`/`THEME`/etc. into `env-config.js` at container start (read by `config.js`), so the same image works against any backend without rebuilding.

```bash
docker build -t self-calendar .
docker run -p 8080:80 -e API_BASE_URL=http://localhost:8082 -e APP_NAME="Self Calendar" self-calendar
# → http://localhost:8080
```

For running the app together with the api, prefer `docker compose up -d --build` from the repo root — see the root [`README.md`](../README.md#quick-start-docker--prod-style).

---
