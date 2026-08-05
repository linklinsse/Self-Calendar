"""
tests/conftest.py
------------------
Shared pytest fixtures for the API test suite.

Settings (DB_URL, SECRET_KEY, ...) are read once at import time by
app.common.config.settings, so the test DB URl/secret must be set via
environment variables *before* app.app is imported anywhere — hence this
happens at module level, above the imports that pull in the app.
"""

import os
import tempfile

os.environ.setdefault("DB_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-a-placeholder-value")
os.environ.setdefault("USER_CREATION", "True")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

# bcrypt's cost is the point in production and pure overhead here: the suite
# registers ~40 users and every hash at the default cost costs ~0.25s, which
# is most of the runtime. Lower the work factor for tests only — before
# app.app is imported, so nothing has captured the default hasher yet.
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

import app.common.security as _security

_security._pwd_hash = PasswordHash((BcryptHasher(rounds=4),))
_security._DUMMY_HASH = _security._pwd_hash.hash("timing-equalisation-dummy")

from app.app import app
from app.common.db_connection import create_db_and_tables, db_engine


@pytest.fixture(scope="session")
def client():
    """A TestClient for the whole test session (triggers lifespan once)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def _migrated_schema():
    """Build the test schema by running the real migrations, once per session.

    Deliberately not SQLModel.metadata.create_all(): that is no longer how
    the application builds its schema, and using it here would test a
    database that no production deployment ever has. A migration that fails
    to produce the schema the models expect should break the suite, not slip
    through because the tests quietly built their own.
    """
    create_db_and_tables()
    yield


@pytest.fixture(autouse=True)
def _clean_db(_migrated_schema):
    """Wipe every table before each test so tests don't see each other's data.

    Depends on the session-scoped schema fixture rather than creating tables
    itself. This is autouse while the `client` fixture is not, so a test that
    never starts the app (the importer's parsing tests, for instance) would
    otherwise hit "no such table".

    Deletes in reverse creation order (children before parents) since
    PRAGMA foreign_keys=ON is active on this connection.
    """
    with db_engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


def register_and_login(client: TestClient, username: str, password: str = "supersecret123") -> str:
    """Register a user (ignoring "already exists") and return a bearer token."""
    client.post("/auth/register", json={"username": username, "password": password})
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
