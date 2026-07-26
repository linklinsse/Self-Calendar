# Self Calendar API

A personal calendar REST API built with [FastAPI](https://fastapi.tiangolo.com/) and [SQLModel](https://sqlmodel.tiangolo.com/).  
It allows users to manage their own calendars, share them with others using a role-based permission system, and create time-ranged events.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Permission System](#permission-system)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Run in Development Mode](#run-in-development-mode)
  - [Run with Docker](#run-with-docker)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Development Commands](#development-commands)
- [Known Limitations & TODOs](#known-limitations--todos)

---

## Features

- User registration and authentication via Bearer token (JWT)
- Create, read, update and delete **calendars**
- Share calendars with other users via a **permission system** (`R` / `W` / `O`)
- Create, read, update and delete **events** inside calendars
- **Recurring events** (daily/weekly/monthly/yearly) with per-occurrence exceptions
- Query events within a **date range**, across multiple calendars, with optional category filtering
- Manage user–calendar memberships (`/user_calendar`)
- Category management per calendar (`/category`)

---

## Tech Stack

| Layer       | Technology                                           |
|-------------|------------------------------------------------------|
| Framework   | [FastAPI](https://fastapi.tiangolo.com/) ≥ 0.128     |
| ORM         | [SQLModel](https://sqlmodel.tiangolo.com/) ≥ 0.0.33  |
| Database    | SQLite (development) — swappable via `DB_URL` in `.env` |
| Recurrence dates | [python-dateutil](https://dateutil.readthedocs.io/) (month/year interval math) |
| Python      | 3.12+                                                |
| Package mgr | [uv](https://github.com/astral-sh/uv)                |
| Linter      | [Ruff](https://docs.astral.sh/ruff/)                 |
| Containers  | Docker                                               |

---

## Project Structure

```
api/
├── app/
│   ├── app.py                              # FastAPI instance, lifespan, router registration
│   ├── common/
│   │   ├── config.py                       # Typed settings loaded from .env
│   │   ├── db_connection.py                # Engine, session factory, SessionDep
│   │   ├── enums.py                        # CalendarRight, EventRecurenceType/EndType enums
│   │   ├── errors.py                       # Central error catalogue — raise_app_error(AppErrorCode.X)
│   │   ├── security.py                     # OAuth2 scheme, JWT encode/decode, password hashing
│   │   ├── contexts/
│   │   │   └── logged_user_context.py      # Request-scoped user context (ContextVar)
│   │   ├── decorators/
│   │   │   └── db_session_injector.py      # Tombstone — decorator removed, see file for rationale
│   │   ├── dependencies/
│   │   │   └── verify_logged_user_dependency.py  # Decodes token, populates user context
│   │   ├── middleware/
│   │   │   └── rate_limit_middleware.py    # Per-IP failure counter for /auth/login, /auth/register
│   │   └── utils/
│   │       └── verify_user_right_calendar.py     # Permission level check helper
│   ├── models/                             # SQLModel table definitions (DB layer)
│   │   ├── obj_user_model.py
│   │   ├── obj_calendar_model.py
│   │   ├── lnk_user_calendar_model.py
│   │   ├── obj_event_model.py
│   │   ├── obj_event_recurence_model.py
│   │   ├── obj_event_recurence_exception_model.py
│   │   └── obj_category_model.py
│   ├── schemas/                            # Pydantic schemas (request / response bodies)
│   │   ├── common_fields.py
│   │   ├── auth_schema.py
│   │   ├── obj_user_schema.py
│   │   ├── obj_calendar_schema.py
│   │   ├── lnk_user_calendar_schema.py
│   │   ├── obj_event_schema.py
│   │   ├── obj_event_recurence_schema.py
│   │   ├── obj_event_recurence_exception_schema.py
│   │   └── obj_category_schema.py
│   ├── services/                           # Business logic
│   │   ├── auth_service.py
│   │   ├── obj_user_service.py
│   │   ├── obj_calendar_service.py
│   │   ├── lnk_user_calendar_service.py
│   │   ├── obj_event_service.py
│   │   ├── obj_event_recurente_service.py
│   │   └── obj_category_service.py
│   └── routing/                            # FastAPI routers (HTTP handlers)
│       ├── auth_routing.py
│       ├── user_routing.py
│       ├── calendar_routing.py
│       ├── user_calendar_routing.py
│       ├── event_routing.py                # Includes recurrence exception delete
│       └── category_routing.py
├── bruno/                                  # Bruno API collection (local HTTP client)
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

---

## Permission System

Calendars use a three-level permission system stored in the `CalendarRight` enum.  
Each user–calendar pair is stored in the `lnk_user_calendar` table with a `right` field:

| Code | Name  | Capabilities                                                        |
|------|-------|---------------------------------------------------------------------|
| `R`  | Read  | Read the calendar and its events                                    |
| `W`  | Write | All of the above + create, edit and delete events                   |
| `O`  | Owner | All of the above + edit/delete the calendar itself, manage members  |

Permissions are ordered: `R < W < O`. A check for level `W` will also pass for an `O` user.

When a user creates a calendar, they are automatically assigned the `O` (Owner) role.

Every calendar object returned by the API (`POST/GET/PATCH /calendar/...`) includes a `user_right` field with the calling user's permission level on that calendar, so clients can conditionally show owner-only UI (e.g. calendar settings, member management) without an extra request.

---

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) — fast Python package manager

```bash
# Install uv (if not already installed)
curl -Ls https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd api

# Install dependencies (including dev tools)
make init
# or manually:
uv venv
uv sync --dev
```

### Run in Development Mode

```bash
make dev
# or manually:
uv run fastapi dev app/app.py
```

The API will be available at `http://localhost:8000`.  
Interactive documentation (Swagger UI) is at `http://localhost:8000/docs`.  
Alternative docs (ReDoc) are at `http://localhost:8000/redoc`.

### Run with Docker

```bash
# Build the image
make docker-build

# Run the container
docker run -p 8082:8082 fastapi-app
```

The API will be available at `http://localhost:8082`.

---

## API Reference

All routes except `/auth/login` and `/auth/register` require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Authentication

| Method | Path              | Auth | Description                        |
|--------|-------------------|------|------------------------------------|
| POST   | `/auth/login`     | —    | Log in and receive a JWT token     |
| POST   | `/auth/register`  | —    | Create a new user account          |
| GET    | `/auth/me`        | ✓    | Return the current user's profile  |

### User

| Method | Path              | Auth | Description                              |
|--------|-------------------|------|------------------------------------------|
| PATCH  | `/user/password`  | ✓    | Change the current user's password       |

### Calendars

| Method | Path                    | Permission | Description                    |
|--------|-------------------------|------------|--------------------------------|
| POST   | `/calendar/`            | ✓          | Create a new calendar          |
| GET    | `/calendar/`            | R          | List all accessible calendars  |
| GET    | `/calendar/{id}`        | R          | Get a single calendar          |
| PATCH  | `/calendar/{id}`        | O          | Update calendar metadata       |
| DELETE | `/calendar/{id}`        | O          | Delete a calendar              |

### Events

| Method | Path                           | Permission | Description                          |
|--------|--------------------------------|------------|----------------------------------------|
| POST   | `/event/`                      | W          | Create an event (optionally recurring) |
| GET    | `/event/range`                 | R          | Get events in a date range, across one or more calendars |
| GET    | `/event/{id}`                  | R          | Get a single event                    |
| PATCH  | `/event/{id}`                  | W          | Update an event                       |
| DELETE | `/event/{id}`                  | W          | Delete an event (and its recurrence, if any) |
| DELETE | `/event/{id}/{date}`           | W          | Exclude one occurrence of a recurring event (adds an exception, does not delete the series) |

Query parameters for `GET /event/range` (repeat `calendar_ids`/`category_ids` for multiple values):

| Parameter      | Type                 | Required | Description                        |
|----------------|----------------------|----------|-------------------------------------|
| `calendar_ids` | string (repeatable)  | No       | Restrict to these calendars (default: none, i.e. no results) |
| `from_date`    | integer              | No       | Range start (Unix timestamp, default: 0) |
| `to_date`      | integer              | No       | Range end (Unix timestamp, default: unbounded) |
| `category_ids` | string (repeatable)  | No       | Filter by category                 |

#### Recurring events

Pass `obj_recurence` on create/edit to make an event recurring:

```json
{
  "type": "D | W | M | Y",
  "interval": 1,
  "days": "1111100",
  "endType": "N | C | U",
  "count": 5,
  "until": 1735689600
}
```

`days` is a 7-character Monday-first bitmask (weekly recurrence only). `endType` is `N` (never), `C` (after `count` occurrences), or `U` (until a given Unix timestamp). Editing an event's `obj_recurence` replaces the recurrence rule wholesale (the old one is deleted, a new one is created) — editing any other field leaves an existing recurrence untouched.

### Categories

| Method | Path                              | Permission | Description                       |
|--------|-----------------------------------|------------|-----------------------------------|
| POST   | `/category/`                      | W          | Create a category in a calendar   |
| GET    | `/category/calendar/{calendar_id}`| R          | List all categories in a calendar |
| GET    | `/category/{id}`                  | R          | Get a single category             |
| PATCH  | `/category/{id}`                  | W          | Update a category                 |
| DELETE | `/category/{id}`                  | W          | Delete a category                 |

### User–Calendar Memberships

| Method | Path                              | Permission | Description                        |
|--------|-----------------------------------|------------|------------------------------------|
| POST   | `/user_calendar/`                 | O          | Add a user to a calendar           |
| GET    | `/user_calendar/all/{calendar_id}`| R          | List all members of a calendar     |
| GET    | `/user_calendar/{id}`             | R          | Get a single membership record     |
| PATCH  | `/user_calendar/{id}`             | O          | Update a member's permission level |
| DELETE | `/user_calendar/{id}`             | O          | Remove a user from a calendar      |

---

## Configuration

All configuration is managed through environment variables, loaded from `conf/.env`.  
Copy the example below to `conf/.env` and adjust the values:

```env
# conf/.env

# Set to false to disable public user registration
USER_CREATION=true

# Generate a strong random secret for production — never use the default
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SQLite for development; swap to PostgreSQL for production
DB_URL=sqlite:///./dev.db
# DB_URL=postgresql+psycopg2://user:password@host/dbname

# Comma-separated list of allowed CORS origins.
# Empty by default — no cross-origin requests are permitted.
# A warning is printed at startup for every origin listed here.
# CORS_ORIGINS=http://localhost:5173,https://app.example.com

# ── Rate limiting ────────────────────────────────────────────────────────
# Consecutive failures from one IP before it is blocked (default: 5)
RATE_LIMIT_MAX_FAILURES=5
# How long the block lasts in seconds (default: 180 = 3 minutes)
RATE_LIMIT_TIMEOUT_SECONDS=180
```

To switch to PostgreSQL, update `DB_URL` — no source code changes are required.

---

## Development Commands

```bash
make help         # Show all available commands
make init         # Install all dependencies
make dev          # Start development server with auto-reload
make lint         # Run Ruff linter and formatter check
make lint-fix     # Run Ruff with auto-fix
make test         # Run test suite (pytest)
make docker-build # Build Docker image
```

---

## Known Limitations & TODOs

- **`ObjEventModel.category_id` is not a real foreign key** — a category can be deleted (directly, via `DELETE /category/{id}`) while events still reference its id (dangling reference, no integrity check). Note: deleting a whole *calendar* does cascade-delete its categories and events together, so this only applies to deleting a category on its own.
- **Recurrence editing always replaces the rule wholesale** — `edit_event` deletes the old `ObjEventRecurenceModel` row and creates a new one whenever `obj_recurence` is provided, rather than patching it in place. Functionally correct but churns rows; `obj_event_recurente_service.update_event_recurence` exists commented-out as a starting point for a real partial-update.
- **`SECRET_KEY` default is insecure** — the fallback value `"change-me"` must be overridden in any non-local environment via the `.env` file.
