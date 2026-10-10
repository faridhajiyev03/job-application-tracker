# T3 — independent initial QA

Assessment: **FAIL — one blocking database-isolation defect.** Runtime tests are
unverified; no test passed or ran. Implementation otherwise meets the requested
initial coverage by static inspection.

Reviewer: independent `qa_reviewer` agent `foundation_qa`. Skills used:
backend-code-review, backend-security-review (database safety scope), and
backend-verification, including their reference checklists. No implementation
files edited. No further agents launched.

## Inputs and scope

Read the original objective and safety requirements, complete
`tests/IMPLEMENTATION_REPORT.md`, and `.task-records/backend-foundation.md`.
Confirmed branch `test/backend-foundation`; coordinator baseline was clean.
Inspected tracked unstaged diff, empty staged diff, and all new configuration,
test Python files, documentation and ignore files. Read surrounding database,
security, main, routers, services, models and schemas plus dependency pins.
No application or migration changes appear in the diff/status.

## Finding F1 — high, blocking: ambient libpq client defaults can escape isolation

Location: `tests/conftest.py:84`, `tests/conftest.py:112`,
`tests/conftest.py:114`, and `tests/conftest.py:120`.

The PG-variable filtering at line 84 builds an environment only for `initdb` and
`pg_ctl`. It does not sanitize the Python process environment used by psycopg,
including SQLAlchemy's psycopg connections. Those calls specify `host`, user and
database but omit `hostaddr`, service isolation, and port. An inherited
`PGHOSTADDR` or `PGSERVICE` resolving to a service with `hostaddr` can direct the
connection to TCP on an existing/production server even with the explicit Unix
socket `host`. The initial admin call attempts connection before any SQL safety
verification. Successful authentication as `jat_test` can then create/drop a
random database on that server. Even unsuccessful authentication violates the
requirement never to connect to production. Ambient `PGPORT` can independently
cause a socket mismatch since the server subprocess no longer inherits it.

This is a confirmed code/defaults defect, not an observed production connection;
no connection was attempted during review. Official libpq documentation says
PGHOSTADDR supplies the hostaddr default, service files supply omitted connection
parameters, and nonempty hostaddr always selects TCP and takes precedence over
host. Sources: [environment variables](https://www.postgresql.org/docs/17/libpq-envars.html),
[service files](https://www.postgresql.org/docs/15/libpq-pgservice.html),
[connection parameters](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-HOSTADDR).

Required correction: enforce the isolation boundary for the Python client
environment throughout cluster setup, connections, and teardown; remove/reject
ambient PG defaults including services and hostaddr before any libpq use, and
explicitly choose the same port for server/admin/SQLAlchemy. Prevent fallback to
ambient password/service configuration. Add a nonconnecting regression check
with synthetic PGHOSTADDR, PGSERVICE/PGSERVICEFILE and PGPORT values proving they
cannot influence client settings. Update documentation and handoff evidence.

## Positive static isolation evidence

- DATABASE_URL is replaced with a sentinel before test application imports;
  dotenv is disabled/patched and already imported application modules fail closed.
- The original engine gets a creator that raises, and request dependencies use
  the generated engine with one SQLAlchemy session per request.
- `initdb` targets a fresh private directory, TCP listening is disabled, Unix
  socket permissions are restrictive, and no external URL override is accepted.
- Each test gets a random new database; real service commit/rollback is allowed.
  Engine disposal precedes per-database drop; session teardown stops only the
  freshly initialized cluster. Identifier composition is safe.
- No SQLite fallback or migration execution exists. ORM metadata initializes
  schema only, so migration correctness is not covered.
- These static strengths do not resolve F1 or establish executed lifecycle safety.

## Acceptance status

| Criterion | Status | Evidence |
| --- | --- | --- |
| Existing backend inspected | Met | Application/dependency/model/database code read |
| Pytest configuration and fixtures implemented | Met statically | pytest.ini, requirements-test.txt, tests/conftest.py |
| Disposable PostgreSQL isolation | Unmet | F1 must be corrected; lifecycle unexecuted |
| Registration/login tests | Met statically, runtime unverified | Positive normal/API paths, hash/privacy, duplicate and invalid inputs |
| Invalid authentication tests | Met statically, runtime unverified | Invalid login, nine token/header variants, anonymous CRUD routes |
| Cross-user application tests | Met statically, runtime unverified | Read/update/delete hidden and data unchanged; list/summary ownership |
| Independent actual-diff review | Met | This review includes untracked source and surrounding code |
| Safe runtime validation | Blocked | Missing pytest/app packages and F1; no DB tests executed |
| Preserve app/migrations; no installs/commit/push/deploy | Met | Observed diff and performed operations |

33 parametrized cases are authored by source inspection (18 authentication,
13 application authorization, 2 harness isolation). This is not a collection
result. Assertions align with inspected current route/schema/service behavior.

## Checks actually executed

- `python3 -c 'import importlib.util; print({name: importlib.util.find_spec(name) is not None for name in ("pytest", "sqlalchemy", "fastapi", "psycopg", "httpx", "jwt", "dotenv")})'`
  — exit 0; all seven modules absent in available Python 3.13.
- `python3 -c 'import ast; from pathlib import Path; paths = sorted(Path("tests").glob("*.py")); [ast.parse(p.read_text(), filename=str(p)) for p in paths]; print("AST parse PASS:", ", ".join(map(str, paths)))'`
  — exit 0; all four Python test/harness files parse.
- `git diff --check` — exit 0, no whitespace errors in tracked diff.
- `python3 -m pytest --collect-only -q` — exit 1, `No module named pytest`;
  zero collected/executed tests, no runtime pass claim.
- `git branch --show-current`, `git status --short`, `git diff`,
  `git diff --name-only`, `git diff --cached --stat` — exit 0; branch confirmed,
  only expected new tests/config/reports plus .gitignore, no staged changes.

`pytest --run-db` and all database-dependent checks were NOT RUN. No packages,
database server, database connection or migrations were installed/started/run.
No existing DATABASE_URL or PG secret values were inspected or used. No
configured lint/type/security scanner was run. AST success is syntax evidence,
not import/dependency compatibility evidence.

## Remaining coverage and operational limitations

Beyond F1, no additional blocking implementation defect was established.
Dependency compatibility, collection, PostgreSQL startup/teardown, schema
creation, and HTTP assertions remain unverified. No preexisting failure is
claimed beyond missing local prerequisites. Initial suite does not cover
registration races/SQLSTATE branch through the API, migration upgrades,
concurrency, filter/pagination combinations, ownership-field injection, or all
validation failures; these are future coverage, not required foundation blockers.
Abrupt process termination can leave an isolated local cluster/artifacts, as
documented. Default invocation skips all current tests when pytest is installed;
runtime CI must explicitly opt into DB tests and inspect skips. Re-review F1
after a bounded developer fix; do not execute integration tests until safe.
