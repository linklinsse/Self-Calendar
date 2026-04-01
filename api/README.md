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
- [Known Limitations & TODOs](#known-limitations--todos)

---

## Features

- User authentication via Bearer token
- Create, read, update and delete **calendars**
- Share calendars with other users via a **permission system** (`C` / `P` / `O`)
- Create, read, update and delete **events** inside calendars
- Query events within a **date range** with optional category filtering
- Manage user–calendar memberships (`/user_calendar`)

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|--------------------------------------------------|
| Framework   | [FastAPI](https://fastapi.tiangolo.com/) ≥ 0.128 |
| ORM         | [SQLModel](https://sqlmodel.tiangolo.com/) ≥ 0.0.33 |
| Database    | SQLite (development) — swappable via `db_connection.py` |
| Python      | 3.12+                                            |
| Package mgr | [uv](https://github.com/astral-sh/uv)           |
| Linter      | [Ruff](https://docs.astral.sh/ruff/)            |
| Containers  | Docker                                           |

---

## Project Structure

```
api/
├── app/
│   ├── app.py                          # FastAPI instance, router registration, startup
│   ├── common/
│   │   ├── db_connection.py            # SQLite engine, session factory, SessionDep
│   │   ├── security.py                 # OAuth2 scheme, token encode/decode, password hashing
│   │   ├── contexts/
│   │   │   └── loged_user_context.py   # Request-scoped user context (ContextVar)
│   │   ├── decorators/
│   │   │   └── db_session_injector.py  # Decorator that injects a DB session automatically
│   │   ├── dependencies/
│   │   │   ├── verify_loged_user_dependency.py      # Rejects unauthenticated requests
│   │   │   └── fill_loged_user_context_dependency.py # Populates the user context from token
│   │   └── utils/
│   │       └── verif_user_right_calendar.py  # Permission level check helper
│   ├── models/                         # SQLModel table definitions (DB layer)
│   │   ├── obj_user_model.py
│   │   ├── obj_calendar_model.py
│   │   ├── lnk_user_calendar_model.py
│   │   └── obj_event_model.py
│   ├── schemas/                        # Pydantic schemas (request / response bodies)
│   │   ├── common_fields.py
│   │   ├── obj_user_schema.py
│   │   ├── obj_calendar_schema.py
│   │   ├── lnk_user_calendar_schema.py
│   │   ├── obj_event_schema.py
│   │   ├── obj_category_schema.py
│   │   └── obj_event_recurrence_schema.py
│   ├── services/                       # Business logic
│   │   ├── auth_service.py
│   │   ├── obj_user_service.py
│   │   ├── obj_calendar_service.py
│   │   ├── lnk_user_calendar_service.py
│   │   └── obj_event_service.py
│   └── routing/                        # FastAPI routers (HTTP handlers)
│       ├── auth_routing.py
│       ├── user_routing.py
│       ├── calendar_routing.py
│       ├── user_calendar_routing.py
│       └── event_routing.py
├── bruno/                              # Bruno API collection (local HTTP client)
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

---

## Permission System

Calendars use a three-level permission system. Each user–calendar pair is stored in the `lnk_user_calendar` table with a `right` field:

| Code | Name        | Capabilities                                        |
|------|-------------|-----------------------------------------------------|
| `C`  | Consulter   | Read the calendar and its events                    |
| `P`  | Participer  | All of the above + create, edit and delete events   |
| `O`  | Owner       | All of the above + edit/delete the calendar itself, manage members |

Permissions are ordered: `C < P < O`. A check for level `P` will also pass for an `O` user.

When a user creates a calendar, they are automatically assigned the `O` (Owner) role.

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

All routes except `/auth/login` require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Authentication

| Method | Path          | Description              |
|--------|---------------|--------------------------|
| GET    | `/auth/login` | Log in and get a token   |

### User

| Method | Path        | Description                          |
|--------|-------------|--------------------------------------|
| GET    | `/user/me`  | Return the current user's profile    |

### Calendars

| Method | Path                   | Permission | Description               |
|--------|------------------------|------------|---------------------------|
| POST   | `/calendar/`           | —          | Create a new calendar      |
| GET    | `/calendar/`           | C          | List all accessible calendars |
| GET    | `/calendar/{id}`       | C          | Get a single calendar      |
| PATCH  | `/calendar/{id}`       | O          | Update calendar metadata   |
| DELETE | `/calendar/{id}`       | O          | Delete a calendar          |

### Events

| Method | Path                          | Permission | Description                          |
|--------|-------------------------------|------------|--------------------------------------|
| POST   | `/event/`                     | P          | Create an event                      |
| GET    | `/event/range/{calendar_id}`  | C          | Get events in a date range           |
| GET    | `/event/{id}`                 | C          | Get a single event                   |
| PATCH  | `/event/{id}`                 | P          | Update an event                      |
| DELETE | `/event/{id}`                 | P          | Delete an event                      |

Query parameters for `GET /event/range/{calendar_id}`:

| Parameter     | Type    | Required | Description                            |
|---------------|---------|----------|----------------------------------------|
| `from_date`   | integer | Yes      | Range start (Unix timestamp)           |
| `to_date`     | integer | Yes      | Range end (Unix timestamp)             |
| `category_id` | string  | No       | Filter by category                     |

### User–Calendar Memberships

| Method | Path                            | Description                         |
|--------|---------------------------------|-------------------------------------|
| POST   | `/user_calendar/`               | Add a user to a calendar            |
| GET    | `/user_calendar/all/{cal_id}`   | List all members of a calendar      |
| GET    | `/user_calendar/{id}`           | Get a single membership record      |
| PATCH  | `/user_calendar/{id}`           | Update a member's permission level  |
| DELETE | `/user_calendar/{id}`           | Remove a user from a calendar       |

---

## Configuration

The database URL is configured in `app/common/db_connection.py`.  
By default it uses SQLite (`dev.db` in the working directory).

To switch to PostgreSQL, update the following lines:

```python
# app/common/db_connection.py
db_engine = create_engine("postgresql+psycopg2://user:password@host/dbname")
```

And remove `connect_args` (SQLite-specific).

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

> These are tracked in the source code with `# TODO` comments.

- **Authentication is a stub** — `auth_service.login()` returns a hardcoded token. Real JWT signing/verification (e.g. with `python-jose`) must be implemented in `security.py`.
- **`right` field should be an Enum** — the `LnkUserCalendar` schemas use a plain `str`. A `Literal["R", "W", "O"]` or `Enum` would provide validation.
- **Categories are not implemented** — `ObjCategorySchema` and `category_id` fields exist but there are no model, service or routing counterparts.
- **Recurrences are not implemented** — `ObjEventRecurrenceSchema` and `recurrence_id` exist but are not wired up.
- **`user_right` on `ObjCalendarModel`** — currently declared as `ClassVar` (non-column). It should be populated in the service layer before returning calendar objects to clients.
- **`/auth/login` should be a POST** — GET requests must not mutate state or handle credentials.
- **No cascade deletes** — deleting a calendar does not automatically remove its events or membership records.
