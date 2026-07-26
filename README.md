# Self Calendar

A self-hosted personal calendar: a **FastAPI + SQLModel** REST API and a **Svelte 5 / SvelteKit** frontend (also packaged as an Android/iOS app via Capacitor). Calendars can be shared between users with role-based permissions (Read / Write / Owner), and support one-off and recurring events with per-occurrence exceptions.

This file is the entry point. For implementation detail, see the sub-project docs:

- **[`api/README.md`](api/README.md)** — FastAPI backend: routes, permission model, configuration, dev commands.
- **[`app/README.md`](app/README.md)** — SvelteKit frontend: component/store layout, themes, mobile build, env vars.
- **[`review.md`](review.md)** — living project-review notes (state of the code, known drift, where to look for things). Read this before picking up a new task.

---

## Repository layout

```
Self-Calendar/
├── api/            FastAPI backend (Python 3.12, uv, SQLModel, SQLite)
├── app/            SvelteKit frontend (Svelte 5, Vite, Capacitor for Android/iOS)
├── docker-compose.yml   Builds + runs app (nginx, :8686) + api (:8082) together
├── TODO            Freeform running task/idea list (not an issue tracker)
└── review.md       Project-review notes maintained by the assistant
```

The two sub-projects are independent codebases (separate `package.json` / `pyproject.toml`, separate Makefiles) that only communicate over HTTP — the app talks to the api via `API_BASE_URL`.

---

## Quick start (local dev, no Docker)

```bash
# Terminal 1 — API on http://localhost:8000
cd api
make init
make dev

# Terminal 2 — App on http://localhost:5173
cd app
npm install
npm run dev
```

The app defaults to **mock mode** (sample data, no backend needed). To point it at the local API, create `app/.env.local`:

```env
VITE_MOCK_MODE=false
VITE_API_BASE_URL=http://localhost:8000
```

## Quick start (Docker / prod-style)

```bash
docker compose up -d --build
```

That's it — `docker-compose.yml` builds both images from `api/Dockerfile` and `app/Dockerfile` itself, no separate build step needed. It brings up `SelfCalendar-web` (nginx-served static build, `http://localhost:8686`) and `SelfCalendar-api` (`http://localhost:8082`, called directly by the browser — the web container does not proxy it).

`conf/.env` and `db/` at the repo root are created for you (gitignored) with a freshly generated `SECRET_KEY` and `USER_CREATION=True` so you can register your first account from the app's login screen. **Set `USER_CREATION=False` in `conf/.env` and restart the `api` container once you're done creating accounts** to close public registration. `db/prod.db` is the persisted SQLite database — back it up like any other file.

If you deploy this somewhere other than `localhost` (a real domain, a different host/port), update `API_BASE_URL` in `docker-compose.yml`'s `web.environment` and `CORS_ORIGINS` in `conf/.env` to match, then restart both containers.

---

## High-level architecture

```
┌─────────────┐  JWT bearer  ┌──────────────┐  SQLModel  ┌──────────┐
│  SvelteKit  │ ───────────▶ │   FastAPI    │ ─────────▶ │  SQLite  │
│  app (SPA)  │ ◀─────────── │   api        │ ◀───────── │ dev.db / │
└─────────────┘   JSON       └──────────────┘            │ prod.db  │
                                                            └──────────┘
```

- **Auth**: username/password login → JWT bearer token, stored in `localStorage` on the client (`sc_auth_token`).
- **Permissions**: three-level (`R`/`W`/`O`) per user-per-calendar, enforced in the api service layer via `verify_user_right_calendar`. Each calendar response also carries the caller's own `user_right`, so the app can gate owner-only UI (settings, edit/delete) without a second request.
- **Events**: one-off or recurring (daily/weekly/monthly-style rules, modeled server-side by `ObjEventRecurenceModel` + client-side by `expandEventsForRange` in `app/src/lib/utils.js`). Individual occurrences of a recurring event can be deleted via an exception record without deleting the whole series.
- **Categories**: server-backed CRUD (`/category`), used to color/group events per calendar.
- **Themes**: pure client-side, no server dependency — see `app/README.md`.

For anything more specific — route lists, permission tables, store/component layout — go to the sub-project READMEs; this file intentionally stays high-level so it doesn't drift as fast as the code underneath it.
