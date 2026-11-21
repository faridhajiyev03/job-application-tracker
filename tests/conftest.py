"""Shared test setup.

Database tests run against a separate PostgreSQL database given in
TEST_DATABASE_URL. Its name must end with "_test", so a real database can
never be wiped by mistake. Every test starts with empty tables.
"""

import os

import pytest
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if TEST_DATABASE_URL:
    test_database_name = make_url(TEST_DATABASE_URL).database or ""
    if not test_database_name.endswith("_test"):
        raise RuntimeError(
            "TEST_DATABASE_URL must point to a database whose name ends with '_test'"
        )

# The application reads these settings at import time,
# so they must be set before the application is imported.
os.environ["DATABASE_URL"] = (
    TEST_DATABASE_URL or "postgresql+psycopg://localhost/not_configured_test"
)
os.environ["JWT_SECRET_KEY"] = "test-secret-key-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import models  # noqa: E402,F401  (registers all tables on Base.metadata)
from database import Base, engine  # noqa: E402
from main import app  # noqa: E402

PASSWORD = "test-password-123"


@pytest.fixture(scope="session")
def test_engine():
    """Create all tables once per test run and drop them at the end."""
    if not TEST_DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to run database tests")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_engine(test_engine):
    """Empty every table before each test, so tests never affect each other."""
    with test_engine.begin() as connection:
        connection.execute(
            text("TRUNCATE applications, users RESTART IDENTITY CASCADE")
        )
    return test_engine


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_engine):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def account(client):
    """Register and log in a user; return the user and its auth headers."""

    def create(email="owner@example.com"):
        credentials = {"email": email, "password": PASSWORD}

        registered = client.post("/auth/register", json=credentials)
        assert registered.status_code == 201, registered.text

        logged_in = client.post("/auth/login", json=credentials)
        assert logged_in.status_code == 200, logged_in.text

        token = logged_in.json()["access_token"]
        return registered.json(), {"Authorization": f"Bearer {token}"}

    return create
