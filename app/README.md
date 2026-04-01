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
│   └── +page.svelte            ← Root page → mounts AppShell
│
└── lib/
    ├── config.js               ← All env-var configuration (API, theme, locale)
    ├── utils.js                ← Pure date/time/recurrence helpers
    ├── sampleData.js           ← Demo seed data (used when MOCK_MODE=true)
    │
    ├── stores/                 ← Svelte reactive stores
    │   ├── index.js            ← Public store API (components import from here)
    │   ├── auth.js             ← currentUser, isLoggedIn, authLoading
    │   ├── ui.js               ← view, cursor, overlay states, toast
    │   ├── events.js           ← events list, visibleEvents (filtered), CRUD
    │   ├── calendars.js        ← calendars list, toggle, CRUD
    │   └── categories.js       ← categories list, toggle, CRUD
    │
    ├── services/               ← HTTP service layer (all MOCK_MODE-aware)
    │   ├── api.js              ← Base fetch client + JWT token handling
    │   ├── auth.service.js     ← login / register / logout / getMe
    │   ├── calendar.service.js ← Calendar CRUD + members + params
    │   ├── category.service.js ← Category CRUD
    │   └── event.service.js    ← Event CRUD
    │
    └── themes/                 ← Theme definitions
        ├── index.js            ← Theme registry + resolveTheme / applyTheme
        ├── tokens.js           ← CSS variable names
        ├── blushNoir.js        ← Default (dark rose)
        ├── sageDusk.js         ← Dark mint / forest
        ├── midnightInk.js      ← Deep indigo / lavender
        ├── oceanBreeze.js      ← Dark teal
        ├── sunsetAmber.js      ← Dark amber / warm
        ├── lightClean.js       ← Light neutral
        ├── sunshineYellow.js   ← Light yellow
        └── blossomPink.js      ← Light pink

components/  (under src/lib/components/)
    ├── LoginScreen.svelte
    ├── AppShell.svelte         ← Main layout shell (sidebar + topbar + content)
    ├── Sidebar.svelte          ← Collapsible left sidebar (desktop + mobile drawer)
    ├── Topbar.svelte           ← Header bar with navigation + hamburger
    ├── BottomNav.svelte        ← Mobile-only bottom navigation bar
    │
    ├── calendar/
    │   ├── CalendarBody.svelte ← View dispatcher (month / week / day)
    │   ├── MonthView.svelte    ← Monthly grid
    │   ├── WeekView.svelte     ← 7-column time grid with side-by-side overlap
    │   └── DayView.svelte      ← Single-day time grid with side-by-side overlap
    │
    ├── event/
    │   ├── EventPanel.svelte   ← Add / edit drawer (right on desktop, bottom on mobile)
    │   └── EventModal.svelte   ← Event detail modal
    │
    ├── sidebar/
    │   ├── CalendarList.svelte ← Calendar filter + inline create form
    │   └── CategoryList.svelte ← Category filter + edit
    │
    ├── settings/
    │   ├── CalendarSettings.svelte ← 3-tab modal: General | Members | Params
    │   ├── CategoryEditor.svelte   ← Create / edit a category
    │   └── ThemePicker.svelte      ← Inline theme grid in the sidebar
    │
    └── ui/
        ├── MiniCalendar.svelte ← Date-picker widget used in EventPanel
        ├── FilterDrawer.svelte ← Mobile filter overlay
        ├── ViewSwitcher.svelte ← Month / Week / Day tab strip
        └── Toast.svelte        ← Snackbar notifications
```

---

## Themes

Themes are pure JS objects that define CSS variable values. The active theme is applied at startup via `applyTheme()`, and can be changed at runtime through the ThemePicker in the sidebar.

### Switch the default theme

Open **`src/lib/config.js`** and change `VITE_THEME`, or set it in `.env.local`:

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

All data flows through the service layer in `src/lib/services/`. By default `MOCK_MODE=true` serves sample data with no network calls.

To connect a real API, create `.env.local`:

```env
VITE_MOCK_MODE=false
VITE_API_BASE_URL=https://api.yourdomain.com
```

### Expected API endpoints

| Service                     | Endpoints                                                                    |
|-----------------------------|------------------------------------------------------------------------------|
| `auth.service.js`           | `POST /auth/login` `POST /auth/register` `GET /auth/me` `POST /auth/logout`  |
| `calendar.service.js`       | `GET/POST /calendars` `GET/PUT/DELETE /calendars/:id`                        |
|                             | `GET /calendars/:id/params` `PUT /calendars/:id/params`                      |
|                             | `GET/POST /calendars/:id/members` `PUT/DELETE /calendars/:id/members/:userId`|
| `category.service.js`       | `GET/POST /categories` `PUT/DELETE /categories/:id`                          |
| `event.service.js`          | `GET/POST /events` `PUT/DELETE /events/:id`                                  |

### Authentication

The client uses a JWT bearer token stored in `localStorage` under the key `sc_auth_token`. Set it via `setToken()` from `api.js` on login; it is automatically attached to every request.

### Member object shape

```ts
{
  userId:   string;
  name:     string;
  username: string;   // displayed in the Members tab (@ handle)
  email:    string;   // used for invite flow
  role:     'read' | 'write' | 'admin';
  avatar?:  string;   // optional avatar URL
}
```

### Calendar roles

| Role    | Permissions                                            |
|---------|--------------------------------------------------------|
| `read`  | View events only                                       |
| `write` | View + create / edit / delete events                   |
| `admin` | All of write + manage members + edit calendar settings |

---

## Environment variables

All variables can be set in `.env.local` (gitignored). The defaults work for local development without any backend.

| Variable                 | Default                     | Description                               |
|--------------------------|-----------------------------|-------------------------------------------|
| `VITE_MOCK_MODE`         | `true`                      | Use sample data; set `false` for real API |
| `VITE_API_BASE_URL`      | `http://localhost:3000/api` | Backend API root                          |
| `VITE_THEME`             | `blushNoir`                 | Default theme key                         |
| `VITE_APP_NAME`          | `Self Calendar`             | App name in tab title + login screen      |
| `VITE_DEFAULT_VIEW`      | `month`                     | Starting calendar view                    |
| `VITE_FIRST_DAY_OF_WEEK` | `1` (Monday)                | 0=Sunday, 1=Monday, 6=Saturday            |
| `VITE_LOCALE`            | `en-US`                     | Intl date formatting locale               |

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

## Known fixes (changelog)

| # | Issue | Fix |
|---|-------|-----|
| 1 | All-day events jumping to bottom of time grid | Events with no `start` time are now always treated as all-day, preventing `timeToMinutes(null)` placing them at row ~1400px |
| 2 | Overlapping timed events rendered on top of each other | Added `computeColumns()` in `utils.js` — greedy column layout algorithm; WeekView and DayView both use it |
| 3 | Short events (< 30 min) had unreadable titles | Short blocks now use `font-weight: 700`, hide the time label, and use tighter padding |
| 4 | Calendar/category filters had no effect in week and day view | Converted event lists to `$:` reactive maps so Svelte tracks the `$visibleEvents → expanded → template` dependency chain |
| 5 | Sidebar hamburger button was a no-op on desktop | Sidebar now collapses to `width: 0` on desktop when `sidebarOpen` is false; button works on all breakpoints |
| 6 | Member list showed email as secondary info | Now shows `@username` (falls back to email if no username field present) |
| 7 | README referenced non-existent files and wrong tech stack | Full rewrite: accurate file tree, SvelteKit structure, env vars, API contract, and theme guide |
| 8 | `@sveltejs/kit` missing from `package.json` | Added `@sveltejs/kit`, `svelte-check`, `typescript`; removed conflicting `@sveltejs/vite-plugin-svelte` |
| 9 | `adapter-static` missing `fallback` option | Added `fallback: 'index.html'` so Capacitor SPA routing works correctly |
| 10 | `svelte.config.ts` used Node 21+ `import.meta.dirname` | Simplified to `runes: true` — applies project-wide, no path logic needed |
| 11 | `vite.config.js` used bare `vite` import, no TypeScript | Renamed to `vite.config.ts`, uses `defineConfig` from vite |
| 12 | `src/app.html`, `src/routes/` missing | Created required SvelteKit entry points |
| 13 | `tsconfig.json` missing | Created, extending `.svelte-kit/tsconfig.json` |
| 14 | Makefile `lint` used wrong `jsconfig.json` | Changed to `npm run check` (uses `tsconfig.json`) |
| 15 | Dockerfile content leaked into README | Separated into standalone `Dockerfile` |
