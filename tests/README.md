# Backend test foundation

Use a dedicated Python environment with the application dependencies from
`requirements.txt` plus `requirements-test.txt` (pytest 8 and HTTPX). Installing
these dependencies is a separate, explicitly approved action. Compatibility with
the repository's pinned application versions must be confirmed by execution.

From the repository root:

```sh
python3 -m pytest --collect-only -q
python3 -m pytest -q
python3 -m pytest --run-db -q
```

The default command runs the nonconnecting safety regression and skips database tests. `--run-db` permits the
fixture to initialize a **new** local PostgreSQL cluster using `initdb` and
`pg_ctl` on PATH. Missing application dependencies or PostgreSQL binaries produce
explicit skips. Startup, connection, assertion, and cleanup errors are failures,
not silent skips. No installer or existing database URL is used.

Safety boundary:

- `conftest.py` overwrites DATABASE_URL with an unusable sentinel before application
  imports, supplies a test-only JWT secret, disables dotenv and patches its loader
  during application imports. Pre-imported application modules cause failure.
- The application's default engine has a creator that always raises. Requests use
  a scoped dependency override and a new SQLAlchemy session for each request.
- A unique mode-0700 directory under `tests/.runtime/` holds each cluster. TCP is
  disabled, and PostgreSQL listens only on the private Unix socket. Ambient PG
  settings are removed from the Python process for the entire cluster/client
  lifecycle, including teardown, and from inherited server settings. Only private
  empty password/service files and a private system-service directory are selected.
  Server and clients use the same explicit port, and clients explicitly clear
  hostaddr to enforce Unix-socket transport. Client connection parameters
  explicitly select that socket, the newly initialized role, and database.
- Each test receives a new random database inside that cluster. Real service
  commits and rollbacks are allowed. Isolation does not depend on nested
  transactions. Engines are disposed before each database is dropped, and the
  cluster is stopped and removed at session teardown.
- No migrations are run or changed. ORM metadata creates tables only in new test
  databases, so this suite does not verify migration history.
- Never supply DATABASE_URL or a remote/existing test database. There is no URL
  override option. An interrupted/killed process can leave ignored runtime files;
  do not delete a leftover cluster until confirming its PostgreSQL process stopped.

The test suite covers registration, response privacy, password hashing, login,
invalid bearer tokens, anonymous access, cross-user read/update/delete denial,
list and summary ownership, owner CRUD, and commit/rollback isolation. Race-based
registration conflicts, migration upgrades, concurrent requests, list filtering,
and broader application input validation remain outside this initial foundation.

A nonconnecting hostile-environment regression can run without dependencies:

```sh
python3 -m unittest discover -s tests -p test_database_safety.py -v
```

It supplies synthetic hostile PG defaults, checks their replacement for the full
context lifetime, verifies private empty configuration files and explicit client
parameters, and confirms environment restoration after a simulated failure.
