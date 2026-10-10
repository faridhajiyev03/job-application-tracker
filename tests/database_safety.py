"""Standard-library-only libpq safety boundary; does not open connections."""

from contextlib import contextmanager
import os

TEST_POSTGRES_PORT = 55432


@contextmanager
def isolated_postgres_environment(directory):
    """Remove ambient PG defaults for the complete cluster/client lifecycle."""
    previous = {key: value for key, value in os.environ.items() if key.startswith("PG")}
    passfile = directory / "client.pgpass"
    servicefile = directory / "client.pgservice"
    for path in (passfile, servicefile):
        path.write_text("")
        path.chmod(0o600)
    try:
        for key in tuple(os.environ):
            if key.startswith("PG"):
                del os.environ[key]
        os.environ.update({
            "PGPASSFILE": str(passfile),
            "PGSERVICEFILE": str(servicefile),
            "PGSYSCONFDIR": str(directory),
        })
        yield
    finally:
        for key in tuple(os.environ):
            if key.startswith("PG"):
                del os.environ[key]
        os.environ.update(previous)


def local_connection_parameters(socket, database):
    """Explicit targets shared by admin psycopg and application SQLAlchemy."""
    return {
        "host": str(socket),
        "hostaddr": "",
        "port": TEST_POSTGRES_PORT,
        "user": "jat_test",
        "dbname": database,
        "passfile": str(socket.parent / "client.pgpass"),
    }
