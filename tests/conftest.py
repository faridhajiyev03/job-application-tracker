"""Fail-closed integration harness; never accepts a database URL from outside."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from uuid import uuid4

import pytest

from database_safety import (
    TEST_POSTGRES_PORT,
    isolated_postgres_environment,
    local_connection_parameters,
)

# Install safe configuration before any application module can be collected.
# This URL is deliberately unusable; the application's own engine is blocked too.
os.environ["DATABASE_URL"] = "postgresql+psycopg://test_only@/unusable?host=/nonexistent-jat-tests"
os.environ["JWT_SECRET_KEY"] = "jat-tests-only-secret-never-use-in-production"
os.environ["PYTHON_DOTENV_DISABLED"] = "1"


def pytest_addoption(parser):
    parser.addoption("--run-db", action="store_true",
                     help="Start a new disposable local PostgreSQL cluster")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-db"):
        for item in items:
            if "db" in item.keywords:
                item.add_marker(pytest.mark.skip(
                    reason="Use --run-db for disposable PostgreSQL tests"))


def _run(command, env):
    result = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=60)
    if result.returncode:
        pytest.fail(
            f"Disposable PostgreSQL command failed: {command[0]}\n{result.stdout}\n{result.stderr}")
    return result


def _stop_postgres_and_cleanup(pg_ctl, data, directory, env):
    """Remove cluster files only after PostgreSQL stops successfully."""
    _run(
        [pg_ctl, "-D", str(data), "-m", "immediate", "-w", "stop"],
        env,
    )
    shutil.rmtree(directory)


@pytest.fixture(scope="session")
def app_modules():
    required = ("fastapi", "sqlalchemy", "psycopg", "httpx",
                "jwt", "dotenv", "pwdlib", "email_validator")
    missing = [
        name for name in required if importlib.util.find_spec(name) is None]
    if missing:
        pytest.skip(
            "Missing test dependencies (not installed automatically): " + ", ".join(missing))
    if any(name in sys.modules for name in ("database", "security", "main")):
        pytest.fail("Application was imported before the test safety boundary")

    import dotenv
    import sqlalchemy

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
        original_create_engine = sqlalchemy.create_engine

        def blocked_connection():
            raise RuntimeError(
                "The default application engine is forbidden in tests")

        def blocked_engine(*args, **kwargs):
            return original_create_engine(os.environ["DATABASE_URL"], creator=blocked_connection)

        patch.setattr(sqlalchemy, "create_engine", blocked_engine)
        import main
        import database
        import security
    # The imported engine retains its blocked creator throughout the session.
    yield main.app, database, security
    database.engine.dispose()


@pytest.fixture(scope="session")
def postgres_cluster(app_modules):
    binaries = {name: shutil.which(name) for name in ("initdb", "pg_ctl")}
    if not all(binaries.values()):
        pytest.skip(
            "initdb and pg_ctl are required; no existing database will be used")
    root = Path(__file__).resolve().parent / ".runtime"
    root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="pg-", dir=root))
    data, socket = directory / "data", directory / "s"
    socket.mkdir(mode=0o700)
    if len(str(socket).encode()) > 85:
        shutil.rmtree(directory)
        pytest.skip(
            "Repository path is too long for a private PostgreSQL Unix socket")
    with isolated_postgres_environment(directory):
        env = {key: value for key, value in os.environ.items() if key !=
               "DATABASE_URL"}
        started = False
        try:
            _run([binaries["initdb"], "-D", str(data), "-U", "jat_test",
                 "--auth=trust", "--no-locale", "--encoding=UTF8"], env)
            with (data / "postgresql.conf").open("a") as config:
                escaped_socket = str(socket).replace("'", "''")
                config.write(
                    f"\nport = {TEST_POSTGRES_PORT}\nlisten_addresses = ''\nunix_socket_directories = '{escaped_socket}'\nunix_socket_permissions = 0700\n")
            _run([binaries["pg_ctl"], "-D", str(data), "-l",
                 str(directory / "postgres.log"), "-w", "start"], env)
            started = True
            yield socket
        finally:
            # Stop only our freshly initialized cluster, never a system service.
            if started or (data / "postmaster.pid").exists():
                _stop_postgres_and_cleanup(
                    binaries["pg_ctl"], data, directory, env
                )
            else:
                shutil.rmtree(directory)


@pytest.fixture
def database_factory(postgres_cluster, app_modules):
    import psycopg
    from psycopg import sql
    from sqlalchemy import URL, create_engine

    _, database, _ = app_modules

    @contextmanager
    def fresh_database():
        name = "test_" + uuid4().hex
        with psycopg.connect(**local_connection_parameters(postgres_cluster, "postgres"), autocommit=True) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(name)))
        engine = create_engine(
            URL.create("postgresql+psycopg",
                       username="jat_test", database=name),
            connect_args=local_connection_parameters(postgres_cluster, name),
        )
        try:
            database.Base.metadata.create_all(engine)
            yield engine
        finally:
            engine.dispose()
            with psycopg.connect(**local_connection_parameters(postgres_cluster, "postgres"), autocommit=True) as admin:
                admin.execute(sql.SQL("DROP DATABASE {}").format(
                    sql.Identifier(name)))

    return fresh_database


@pytest.fixture
def db_engine(database_factory):
    with database_factory() as engine:
        yield engine


@pytest.fixture
def db_session(db_engine):
    from sqlalchemy.orm import Session

    with Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_engine, app_modules):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session

    app, database, _ = app_modules
    previous = app.dependency_overrides.copy()

    def isolated_db():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[database.get_db] = isolated_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


@pytest.fixture
def account(client):
    def create(email="owner@example.com"):
        credentials = {"email": email, "password": "test-password-123"}
        registered = client.post("/auth/register", json=credentials)
        assert registered.status_code == 201, registered.text
        logged_in = client.post("/auth/login", json=credentials)
        assert logged_in.status_code == 200, logged_in.text
        return registered.json(), {"Authorization": "Bearer " + logged_in.json()["access_token"]}

    return create
