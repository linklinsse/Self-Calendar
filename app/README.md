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
    │   ├── category.service.js ← Category CRUD (localStorage in live mode, no server endpoint)
    │   └── event.service.js    ← Event CRUD with unix-timestamp serialisation
    │
    └── themes/                 ← Theme definitions
        ├── index.js            ← Theme registry + activeThemeId store + applyTheme()
        ├── tokens.js           ← Shared font, size, radius, and colour tokens
        ├── blushNoir.js        ← Default (dark rose)
        ├── sageDusk.js         ← Dark mint / forest
        ├── midnightInk.js      ← Deep indigo / lavender
        ├── oceanBreeze.js      ← Dark teal
        ├── sunsetAmber.js      ← Dark amber / warm
        ├── lightClean.js       ← Light neutral
        ├── sunshineYellow.js   ← Light yellow
        └── blossomPink.js      ← Light pink
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
| `sunsetAmber`     | 🟠 Amber     | Dark warm             |
| `lightClean`      | ⚪ Neutral   | Light minimal         |
| `sunshineYellow`  | 🌞 Yellow    | Light sunny           |
| `blossomPink`     | 🌺 Pink      | Light blossom         |

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
| `auth.service.js`           | `POST /auth/login` → `{ access_token }` · `GET /auth/me` → user object           |
| `calendar.service.js`       | `GET/POST /calendar/` · `GET/PATCH/DELETE /calendar/{id}`                         |
|                             | `GET/POST /user_calendar/` · `GET/PATCH/DELETE /user_calendar/{id}`               |
| `category.service.js`       | No server endpoint — stored in `localStorage` on the client                       |
| `event.service.js`          | `POST /event/` · `GET /event/range/{calendar_id}?from_date&to_date`               |
|                             | `GET/PATCH/DELETE /event/{id}`                                                    |

> **Note:** There is no registration endpoint. User accounts must be created server-side.

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

| Value   | Permissions                                             |
|---------|---------------------------------------------------------|
| `read`  | View events only                                        |
| `write` | View + create / edit / delete events                    |
| `admin` | All of write + manage members + edit calendar settings  |

The `right` field is set on `UserCalendar` objects returned by `/user_calendar/`. Omitting `right` defaults to full access.

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

---

## Docker

A multi-stage Dockerfile is included. It builds the static assets and serves them with nginx.

```bash
docker build -t self-calendar .
docker run -p 8080:80 self-calendar
# → http://localhost:8080
```

---
