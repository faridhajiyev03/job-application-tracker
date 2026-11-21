# Backend tests

The tests call the API through FastAPI's `TestClient` and use a real
PostgreSQL database.

## What is covered

- Registration, login, and `/auth/me`, including invalid and expired tokens
- Ownership: a user can never read, change, or delete another user's applications
- Creating, updating, and deleting applications, including input validation
- Search, status filter, pagination, and the status summary

## Setup

Create a separate test database. Its name must end with `_test`:

```bash
createdb job_application_tracker_test
```

Install the test dependencies:

```bash
python -m pip install -r requirements-test.txt
```

## Run

```bash
export TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/job_application_tracker_test
python -m pytest -v
```

Without `TEST_DATABASE_URL`, the database tests are skipped.

## How it works

- `conftest.py` points the application at the test database before importing it.
- It refuses any database whose name does not end with `_test`, so a real
  database is never wiped by mistake.
- Tables are created once per run, and every test starts with empty tables.
- GitHub Actions runs the same tests on every push and pull request,
  with PostgreSQL started as a service container.
