# T3 — independent QA, fix cycle 1

Assessment: **F1 resolved by static review and one passing nonconnecting regression.**
One minor scope correction F2 remains; the integration suite is still unverified.
Initial complete findings remain in `qa-initial.md` and are not superseded as an
audit record. Read the full appended developer report before reviewing the actual
updated `conftest.py`, safety helper/test, README, tracked diff, and git status.

## F1 resolution

`tests/database_safety.py` removes every inherited PG-prefixed environment
variable for the context lifetime, then restores the previous values on exit.
Only private empty passfile/servicefile paths and a private system service-config
directory remain. PGSERVICE is absent, so no ambient named service is selected;
private file/directory overrides additionally block standard service/password
fallback. Both admin psycopg connections and SQLAlchemy `connect_args` use the
same helper for socket, blank hostaddr, port 55432, fixed provisioned user,
database, and private passfile. PostgreSQL configuration uses that same port.

The context encloses initdb/start, the session fixture yield and all dependent
database fixtures, and cluster shutdown/removal. Therefore function-fixture
drop/dispose operations occur before PG defaults are restored. No production
target is supplied by the code, and all initial positive isolation observations
remain applicable. No new application or migration edits were introduced.

The hostile-environment regression verifies removal of PGHOSTADDR, PGSERVICE,
PGPORT and other synthetic settings, explicit shared connection parameters,
empty private files, and environment restoration after a synthetic exception.
It does not exercise actual libpq or PostgreSQL; the executed evidence is limited
to the environment/parameter boundary.

## F2 — low severity, repository-only artifact scope

`tests/test_database_safety.py:32` calls `tempfile.TemporaryDirectory()` without
`dir`, so the documented plain unittest command writes temporary pass/service
files in the OS temp directory outside this repository. They are automatically
removed, and this does not present a production database risk. However, the
user's repository-only changes/artifacts constraint is being interpreted
literally by the coordinator. Set `dir=Path(__file__).resolve().parent` (or an
equivalent repository-local runtime directory). This is the only remaining
requested code correction; no further substantive blocking defect was found.

## Checks actually run on cycle-1 files

- `TMPDIR="$PWD/tests" python3 -m unittest discover -s tests -p test_database_safety.py -v`
  — exit 0, **1 test ran and passed**, no database connections. TMPDIR kept this
  review's transient artifacts in the repository while F2 is unresolved.
- `python3 -c 'import ast; from pathlib import Path; paths = sorted(Path("tests").glob("*.py")); [ast.parse(p.read_text(), filename=str(p)) for p in paths]; print("AST parse PASS:", ", ".join(map(str, paths)))'`
  — exit 0, all six helper/harness/test files parse.
- `git diff --check` — exit 0.
- `git diff` and `git status --short` — exit 0, only expected testing/configuration
  and task-record files; no application/migration edits.

No pytest reattempt was needed: initial collection failed with missing pytest,
and no dependency installation occurred. No database-dependent tests ran,
PostgreSQL was not started, no connections were attempted, and no migrations,
installations, commits, pushes or deployment occurred. The review changed only
its own report; no implementation edits.

## Acceptance and remaining limits

Configuration, fixtures, authentication/authorization case coverage, and isolation
design are met statically after F1's fix. Full database isolation behavior,
pytest collection, HTTP assertions and dependency compatibility remain unverified
because prerequisites are absent. Authored count is 33 database-marked cases plus
one nonconnecting unittest (34 by source inspection, not collection).
The same future coverage limits recorded in initial QA remain. Final assessment
for scope compliance awaits the small F2 correction; no need for package installs
or DB execution to validate that correction. One developer/QA fix cycle used.
